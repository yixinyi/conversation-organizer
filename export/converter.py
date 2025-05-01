from utils import convert_latex_to_markdown, sanitize_title
import json
from datetime import datetime
import argparse
from pathlib import Path

"""
This script processes conversation data from a JSON file, extracts messages,
and writes them to markdown files with YAML front matter for Obsidian. It also
creates a summary JSON file with a summary of the conversations. The script is
designed to be run as a command-line interface (CLI), allowing the user to
specify the input JSON file and output directory.

Usage:
    python script.py /path/to/conversations.json /path/to/output_directory
"""


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


def create_file_name(title, conversation_id):
    sanitized_title = sanitize_title(title)
    short_id = conversation_id[:4]
    return f"{sanitized_title} [{short_id}].md"


def check_deleted(deleted_file_name):
    with open(deleted_file_name, "r") as f:
        existing_dirs = set(line.strip() for line in f if line.strip())
    return existing_dirs


def write_messages_to_file(file_path, messages, title, create_time, update_time):
    """
    Writes a markdown file with YAML front matter for Obsidian.
    """
    with file_path.open("w", encoding="utf-8") as file:
        # YAML front matter with metadata
        file.write("---\n")
        file.write(f"title: \"{title}\"\n")
        file.write(f"create_time: \"{create_time}\"\n")
        file.write(f"update_time: \"{update_time}\"\n")
        file.write("tags: [ChatGPT]\n")
        file.write("---\n\n")
        # Write each message
        for message in messages:
            file.write(f"**{message['author']}**\n\n")
            file.write(f"{message['text']}\n\n")


# def write_summary_json(output_dir, summary):
#     summary_json_path = output_dir / "conversation_summary.json"
#     with summary_json_path.open("w", encoding="utf-8") as json_file:
#         json.dump(summary, json_file, ensure_ascii=False, indent=4)


def write_conversations(conversations_data, output_dir, file_with_deleted_names):
    # Ensure the output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    file_path = Path(file_with_deleted_names)
    if not file_path.exists():
        file_path.parent.mkdir(parents=True, exist_ok=True)  # Ensure the directory exists
        file_path.touch()  # Create an empty file

    deleted_dirs = check_deleted(file_with_deleted_names)

    created_files_info = []
    # conversation_summary = []
    for conversation in conversations_data:
        updated = conversation.get("update_time")
        if not updated:
            continue
        updated_date = datetime.fromtimestamp(updated)

        title = conversation.get("title")
        if not title or title.strip() == "":
            title = "Untitled"

        conversation_id = conversation.get("id")

        file_name = create_file_name(title, conversation_id)
        if file_name in deleted_dirs:
            continue
        # Correct if output_dir is a Path object from pathlib and file_name is a string or Path.
        file_path = output_dir / file_name
        messages = get_conversation_messages(conversation)
        create_time_str = datetime.fromtimestamp(conversation.get("create_time")).strftime("%Y-%m-%d %H:%M:%S")
        update_time_str = updated_date.strftime("%Y-%m-%d %H:%M:%S")
        write_messages_to_file(file_path, messages, title, create_time_str, update_time_str)
        # conversation_summary.append({
        #     "title": title,
        #     "create_time": create_time_str,
        #     "update_time": update_time_str,
        #     "file": str(file_path),
        # })
        created_files_info.append({"file": str(file_path)})
    # write_summary_json(output_dir, conversation_summary)
    return created_files_info


def main():
    parser = argparse.ArgumentParser(
        description="Process conversation data from a JSON file and create Obsidian-friendly markdown files.")
    parser.add_argument("input_file", type=Path, help="Path to the input conversations JSON file.")
    parser.add_argument("output_dir", type=Path, help="Directory to save the output files.")
    parser.add_argument("deleted", type=Path, help="Path to the file containing a list of directories to be excluded")
    args = parser.parse_args()
    if not args.input_file.exists():
        print(f"Error: The input file '{args.input_file}' does not exist.")
        return
    with args.input_file.open("r", encoding="utf-8") as file:
        conversations_data = json.load(file)
    created_files_info = write_conversations(conversations_data, args.output_dir, args.deleted)
    for info in created_files_info:
        print(f"Created file: {info['file']}")


if __name__ == "__main__":
    main()

