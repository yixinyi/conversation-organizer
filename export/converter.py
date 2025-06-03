from utils import convert_latex_to_markdown, read_file, sanitize_title
from datetime import datetime
from pathlib import Path
import yaml


def extract_message_parts(message):
    content = message.get("content")
    if content and content.get("content_type") == "text":
        return [convert_latex_to_markdown(part) for part in content.get("parts", [])]
    return []


def get_author_name(message):
    author = message.get("author", {}).get("role", "")
    if author == "assistant":
        return "ChatGPT"
    elif author == "system":
        return "Custom user info"
    return author


def get_conversation_messages(conversation):
    messages = []
    current_node = conversation.get("current_node")
    mapping = conversation.get("mapping", {})
    while current_node:
        node = mapping.get(current_node, {})
        message = node.get("message") if node else None
        if message:
            parts = extract_message_parts(message)
            author = get_author_name(message)
            # Exclude system messages unless explicitly marked
            if parts and len(parts[0]) > 0:
                if author != "system" or message.get("metadata", {}).get("is_user_system_message"):
                    messages.append({"author": author, "text": parts[0]})
        current_node = node.get("parent") if node else None
    return messages[::-1]


def create_file_name_id(conversation_id):
    return f"{conversation_id}.md"


def create_file_name_tile_and_id(title, conversation_id):
    sanitized_title = sanitize_title(title)
    short_id = conversation_id[:4]
    return f"{sanitized_title} [{short_id}].md"


def yaml_data(conversation):
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


def write_conversations(conversations_data, output_dir: Path):
    """
    Converts the conversations in the ChatGPT exported json file to Markdown files with a YAML frontmatter
    """
    # Ensure the output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    created_files_info = []
    for conversation in conversations_data:
        data = conversation_info(conversation)
        file_name = create_file_name_tile_and_id(data["original_title"], data["id"])

        file_path: Path = output_dir / file_name
        messages = get_conversation_messages(conversation)

        with file_path.open("w", encoding="utf-8") as file:
            file.write("---\n")
            yaml.dump(data, file, sort_keys=False)
            file.write("---\n")
            for message in messages:
                file.write(f"**{message['author']}**\n\n")
                file.write(f"{message['text']}\n\n")

        created_files_info.append({"file": str(file_path)})

    return created_files_info
