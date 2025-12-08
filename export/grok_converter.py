import json
import re
from common.utils import find_files_by_id, parse_file
from export.utils import convert_latex_delimiters_excluding_backticks, sanitize_title, format_timestamp
from datetime import datetime
from pathlib import Path
import yaml


# -------------------------------------------------------------------------
# Cleaning Helpers
# -------------------------------------------------------------------------

def remove_grok_tags(text: str) -> str:
    """
    Removes internal Grok rendering tags like:
    <grok:render card_id="..." ...>
      <argument name="citation_id">5</argument>
    </grok:render>
    """
    if not text:
        return ""

    # Regex explanation:
    # <grok:render  -> Matches start of tag
    # .*?           -> Matches any character (non-greedy)
    # </grok:render>-> Matches end tag
    # flags=re.DOTALL -> Allows (.) to match newlines (\n) inside the tag
    pattern = r'<grok:render.*?>.*?</grok:render>'
    return re.sub(pattern, '', text, flags=re.DOTALL)


# -------------------------------------------------------------------------
# Core Extraction Functions
# -------------------------------------------------------------------------

def extract_message_parts(response_data: dict) -> list:
    content = response_data.get("message", "")
    if not content:
        return []

    # 1. Remove the XML/HTML-like Grok tags
    content = remove_grok_tags(content)

    # 2. Clean Latex delimiters
    text = convert_latex_delimiters_excluding_backticks(content)

    return [text]


def get_author_name(response_data: dict) -> str:
    sender = response_data.get("sender")
    if sender == "human":
        return "User"
    # Fallback to model name (e.g. "grok-beta") or generic "Grok"
    return response_data.get("model", "Grok")


def get_conversation_messages(conversation_wrapper: dict) -> list:
    messages = []
    # Assumes 'responses' list is chronologically sorted
    raw_responses = conversation_wrapper.get("responses", [])

    for item in raw_responses:
        data = item.get("response", {})
        parts = extract_message_parts(data)
        author = get_author_name(data)

        # Note: Grok inline citations are usually stripped by the regex above.
        # If Grok adds a metadata field for URLs later, we can extract them here.
        if parts and len(parts[0]) > 0:
            messages.append({
                "author": author,
                "text": parts[0],
                "urls": []
            })
    return messages


def conversation_info(conversation_wrapper: dict) -> dict:
    meta = conversation_wrapper.get("conversation", {})

    conversation_id = meta.get("id")
    conversation_title = meta.get("title") or "Untitled Chat"

    create_time = format_timestamp(meta.get("create_time"))
    update_time = format_timestamp(meta.get("modify_time"))

    messages = get_conversation_messages(conversation_wrapper)
    total_length = sum(len(s['text']) for s in messages)

    data = {
        "id": conversation_id,
        "create_time": create_time,
        "update_time": update_time,
        "original_title": conversation_title,
        "turns": len(messages),
        "characters": total_length,
        "archive": meta.get("starred", False)
    }
    return data


# -------------------------------------------------------------------------
# File Operations
# -------------------------------------------------------------------------

def create_file_name_tile_and_id(title: str, conversation_id: str) -> str:
    sanitized_title = sanitize_title(title)
    return f"{sanitized_title}[{conversation_id}].md"


def write_to_file(metadata: dict, messages: list, file_path: Path) -> None:
    with file_path.open("w", encoding="utf-8") as file:
        file.write("---\n")
        yaml.dump(metadata, file, sort_keys=False)
        file.write("---\n")
        conversation_url = "https://grok.com/c/" + metadata["id"]
        file.write(f"[Conversation url]({conversation_url})\n")
        file.write("\n====================\n\n")

        for message in messages:
            file.write(f"# **{message['author']}**\n\n")
            # If we had URLs, we would loop them here.
            # Since Grok tags are stripped, we just write the text.
            file.write(f"{message['text']}\n\n")

            # Logic preserved if you add URL extraction later
            if message["urls"]:
                file.write("Reference:\n")
                for index, item in message["urls"]:
                    file.write(f"({index}) {item}\n")

            file.write("\n====================\n\n")
        print(f"File created: {file_path}")


def update_file(conversation_wrapper: dict, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    data = conversation_info(conversation_wrapper)

    if not data["id"]:
        return

    existing_file = find_files_by_id(output_dir, data["id"])
    messages = get_conversation_messages(conversation_wrapper)

    if existing_file is not None:
        metadata = parse_file(existing_file)["metadata"]

        # Compare datetimes
        new_ts = datetime.fromisoformat(data['update_time'])

        if isinstance(metadata['update_time'], str):
            old_ts = datetime.fromisoformat(metadata['update_time'])
        else:
            old_ts = metadata['update_time']

        if new_ts > old_ts:
            if metadata.get("delete"):
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


def update_all_files(export_data: dict, output_dir: Path) -> None:
    conversations_list = export_data.get("conversations", [])
    for conv in conversations_list:
        update_file(conv, output_dir)