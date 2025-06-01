from utils import convert_latex_to_markdown, read_file
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


def create_file_name(conversation_id):
    return f"{conversation_id}.md"


def write_messages_to_file(file_path, messages: list, conversation_id, create_time, update_time, title):
    """
    Writes the messages to a markdown file with create time and update time.
    Each message is a dictionary: {'author': 'user or ChatGPT', 'text': 'text'}.
    """
    total_length = sum(len(s['text']) for s in messages)
    yaml_data = {
        "id": conversation_id,
        "create_time": create_time,
        "update_time": update_time,
        "original_title": title,
        "turns": len(messages),
        "characters": total_length
    }
    with file_path.open("w", encoding="utf-8") as file:
        file.write("---\n")
        yaml.dump(yaml_data, file, sort_keys=False)
        file.write("---\n")
        for message in messages:
            file.write(f"**{message['author']}**\n\n")
            file.write(f"{message['text']}\n\n")


def write_conversations(conversations_data, output_dir: Path):
    """
    Converts the conversations in the ChatGPT exported json file to Markdown files.
    """
    # Ensure the output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # This is the file that keeps track of the user-deleted conversations that are to be ignored in future exports
    file_with_deleted_conversations = "deleted_conversations.txt"
    deleted_file_path: Path = output_dir / file_with_deleted_conversations
    if not deleted_file_path.exists():
        deleted_file_path.parent.mkdir(parents=True, exist_ok=True)  # Ensures the directory exists
        deleted_file_path.touch()  # Creates an empty file
    deleted_conversations = read_file(deleted_file_path)

    created_files_info = []
    for conversation in conversations_data:

        conversation_id = conversation.get("id")
        file_name = create_file_name(conversation_id)
        if file_name in deleted_conversations:
            continue

        file_path: Path = output_dir / file_name
        messages = get_conversation_messages(conversation)

        create_time = datetime.fromtimestamp(conversation.get("create_time")).isoformat(timespec="seconds")
        update_time = datetime.fromtimestamp(conversation.get("update_time")).isoformat(timespec="seconds")
        conversation_title = conversation.get("title")
        write_messages_to_file(file_path, messages, conversation_id, create_time, update_time, conversation_title)

        created_files_info.append({"file": str(file_path)})

    return created_files_info




