import json
from common.utils import find_files_by_id, parse_file
from export.utils import convert_latex_delimiters_excluding_backticks, sanitize_title, clean_text
from datetime import datetime
from pathlib import Path
import yaml


def extract_message_parts(message: dict) -> list:
    """
    Extracts the main text content from a message.

    Special handling is included for system tool messages:
    - canmore.create_textdoc: returns the 'content' field (full new doc)
    - canmore.update_textdoc: returns the 'replacement' field (code update)

    If decoding fails or the message is normal, falls back to raw text.
    """
    content = message.get("content")
    if not content or content.get("content_type") != "text":
        return []

    parts = content.get("parts", [])
    if not parts:
        return []

    text = convert_latex_delimiters_excluding_backticks(parts[0])
    recipient = message.get("recipient")

    if recipient == "canmore.create_textdoc":
        try:
            doc = json.loads(text)
            lang = doc.get("type", "").split("/")[-1]
            content = doc.get('content', '')
            return [f"```{lang}\n{content}\n```"]
        except (json.JSONDecodeError, TypeError):
            pass
    if recipient == "canmore.update_textdoc":
        try:
            parsed = json.loads(text)
            updates = parsed.get("updates", [])
            if updates and "replacement" in updates[0]:
                content = updates[0]["replacement"]
                return [f"```\n{content}\n```"]
        except json.JSONDecodeError:
            pass
    return [text]


def get_author_name(message: dict) -> str:
    author = message.get("author", {}).get("role", "")
    if author == "assistant":
        meta = message.get("metadata", {})
        model_slug = meta.get("model_slug")
        return model_slug
    elif author == "system":
        return "Custom user info"
    return author


def get_conversation_messages(conversation: dict) -> list:
    messages = []
    current_node = conversation.get("current_node")
    mapping = conversation.get("mapping", {})
    while current_node:
        node = mapping.get(current_node, {})
        message = node.get("message") if node else None
        if message:
            parts = extract_message_parts(message)
            author = get_author_name(message)
            urls = extract_search_result_urls(message)
            if author != "tool":
                # Exclude system messages unless explicitly marked
                if parts and len(parts[0]) > 0:
                    if author != "system" or message.get("metadata", {}).get("is_user_system_message"):
                        messages.append({"author": author, "text": parts[0], "urls": urls})
        current_node = node.get("parent") if node else None
    return messages[::-1]


def extract_search_result_urls(message: dict) -> list:
    urls = []
    real_author = message.get("author", {}).get("metadata", {}).get("real_author")
    if real_author == "tool:web":
        for group in message.get("metadata", {}).get("search_result_groups", []):
            for entry in group.get("entries", []):
                url = entry.get("url", [])
                if url:
                    ref_id = entry.get("ref_id", [])
                    if ref_id:
                        ref_index = ref_id.get("ref_index")
                        urls.append((ref_index, url))
    return urls


def create_file_name_id(conversation_id: str) -> str:
    return f"{conversation_id}.md"


def create_file_name_tile_and_id(title: str, conversation_id: str) -> str:
    sanitized_title = sanitize_title(title)
    return f"{sanitized_title}[{conversation_id}].md"


def conversation_info(conversation: dict) -> dict:
    messages = get_conversation_messages(conversation)
    conversation_id = conversation.get("id")
    create_time = datetime.fromtimestamp(conversation.get("create_time")).isoformat(timespec="seconds")
    update_time = datetime.fromtimestamp(conversation.get("update_time")).isoformat(timespec="seconds")
    conversation_title = conversation.get("title")
    is_archived = conversation.get("is_archived")

    # Each message is a dictionary: {'author': 'user' or 'ChatGPT', 'text': 'text'}
    total_length = sum(len(s['text']) for s in messages)

    data = {
        "id": conversation_id,
        "create_time": create_time,
        "update_time": update_time,
        "original_title": conversation_title,
        "turns": len(messages),
        "characters": total_length,
        "archive": is_archived
    }
    return data


def write_to_file(metadata: dict, messages: list, file_path: Path) -> None:
    with file_path.open("w", encoding="utf-8") as file:
        file.write("---\n")
        yaml.dump(metadata, file, sort_keys=False)
        file.write("---\n")
        conversation_url = "https://chatgpt.com/c/" + metadata["id"]
        file.write(f"[Conversation url]({conversation_url})\n")
        file.write("\n====================\n\n")
        for message in messages:
            file.write(f"# **{message['author']}**\n\n")
            urls = message["urls"]
            if urls:
                file.write(f"{clean_text(message['text'])}\n\n")
                file.write("Reference:\n")
                urls.sort(key=lambda t: t[0])
                for index, item in urls:
                    file.write(f"({index}) {item}\n")
            else:
                file.write(f"{message['text']}\n\n")
            file.write("\n====================\n\n")
        print(f"File created: {file_path}")


def update_file(conversation: dict, output_dir: Path) -> None:
    # Ensure the output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    data = conversation_info(conversation)
    existing_file = find_files_by_id(output_dir, data["id"])
    messages = get_conversation_messages(conversation)
    if existing_file is not None:
        metadata = parse_file(existing_file)["metadata"]
        new_update_time = datetime.fromisoformat(data['update_time'])
        if type(metadata['update_time']) == str:
            old_update_time = datetime.fromisoformat(metadata['update_time'])
        else:
            old_update_time = metadata['update_time']
        if new_update_time > old_update_time:
            # If a file is marked delete, but it got modified on the web-end,
            # then we add a delete_time that is the old update_time
            if "delete" in metadata:
                if metadata["delete"]:
                    metadata["delete_time"] = metadata["update_time"]
            else:
                metadata["delete"] = False
            metadata.update(data)
            write_to_file(metadata, messages, existing_file)
    else:
        file_name = create_file_name_tile_and_id(data["original_title"], data["id"])
        file_path: Path = output_dir / file_name
        data["delete"] = False
        write_to_file(data, messages, file_path)


def update_all_files(conversations: dict, output_dir: Path) -> None:
    for conversation in conversations:
        update_file(conversation, output_dir)
