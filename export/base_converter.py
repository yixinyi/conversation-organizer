import re
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
import yaml

from common.utils import find_files_by_id, parse_file
from export.utils import sanitize_title, format_timestamp


# -------------------------------------------------------------------------
# Custom YAML representer: force datetime-like strings to be quoted
# so that yaml.safe_load always returns them as strings, not datetime objects.
# This prevents cross-platform differences in YAML parsing (e.g. Windows vs Mac).
# -------------------------------------------------------------------------

_ISO_DATETIME_RE = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}')


def _timestamp_str_representer(dumper, data):
    """Quote strings that look like ISO timestamps to prevent YAML from parsing them as datetime."""
    if _ISO_DATETIME_RE.match(data):
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='"')
    return dumper.represent_str(data)


yaml.add_representer(str, _timestamp_str_representer)


# -------------------------------------------------------------------------
# Base Exporter Class
# -------------------------------------------------------------------------

class BaseConversationExporter(ABC):
    """
    Abstract base class for conversation exporters from different platforms.
    
    Subclasses must implement:
    - extract_message_parts(message_data: dict) -> list
    - get_author_name(message_data: dict) -> str
    - get_conversation_url_prefix() -> str
    - get_conversation_messages(conversation: dict) -> list
    
    Optional overrides:
    - extract_urls_from_message(message_data: dict) -> list
    - clean_text(text: str) -> str
    """

    # =====================================================================
    # Abstract Methods (Platform-Specific)
    # =====================================================================

    @abstractmethod
    def extract_message_parts(self, message_data: dict) -> list:
        """
        Extract and process the text content from a single message.
        Returns a list of text parts (usually single item).
        """
        pass

    @abstractmethod
    def get_author_name(self, message_data: dict) -> str:
        """
        Extract the author/sender name from a message.
        """
        pass

    @abstractmethod
    def get_conversation_url_prefix(self) -> str:
        """
        Return the base URL prefix for conversations on this platform.
        E.g., "https://chatgpt.com/c/" or "https://grok.com/c/"
        """
        pass

    @abstractmethod
    def get_conversation_messages(self, conversation: dict) -> list:
        """
        Extract all messages from a conversation object.
        Returns a list of dicts with keys: author, text, urls
        """
        pass

    # =====================================================================
    # Optional Overrides (Hooks)
    # =====================================================================

    def extract_urls_from_message(self, message_data: dict) -> list:
        """
        Extract URLs/citations from a message. Override if platform supports it.
        Returns a list of (index, url) tuples.
        """
        return []

    def clean_text(self, text: str) -> str:
        """
        Clean text before writing. Override if needed.
        """
        return text

    # =====================================================================
    # Shared Implementation
    # =====================================================================

    def create_file_name_tile_and_id(self, title: str, conversation_id: str) -> str:
        """Create markdown filename from title and ID."""
        sanitized_title = sanitize_title(title)
        return f"{sanitized_title}[{conversation_id}].md"

    def conversation_info(self, conversation: dict, messages: list) -> dict:
        """Build metadata dict for a conversation."""
        conversation_id = self._extract_conversation_id(conversation)
        conversation_title = self._extract_conversation_title(conversation)
        create_time = self._extract_create_time(conversation)
        update_time = self._extract_update_time(conversation)
        is_archived = self._extract_is_archived(conversation)

        total_length = sum(len(s['text']) for s in messages)

        data = {
            "id": conversation_id,
            "create_time": format_timestamp(create_time),
            "update_time": format_timestamp(update_time),
            "original_title": conversation_title,
            "turns": len(messages),
            "characters": total_length,
            "archive": is_archived
        }
        return data

    # Hooks for extracting metadata from different conversation formats
    def _extract_conversation_id(self, conversation: dict) -> str:
        """Override if ID is stored differently."""
        return conversation.get("id", "")

    def _extract_conversation_title(self, conversation: dict) -> str:
        """Override if title is stored differently."""
        return conversation.get("title", "Untitled Chat")

    def _extract_create_time(self, conversation: dict):
        """Override if timestamp is stored differently."""
        return conversation.get("create_time")

    def _extract_update_time(self, conversation: dict):
        """Override if timestamp is stored differently."""
        return conversation.get("modify_time")

    def _extract_is_archived(self, conversation: dict) -> bool:
        """Override if archive flag is stored differently."""
        return conversation.get("is_archived", False)

    def write_to_file(self, metadata: dict, messages: list, file_path: Path) -> None:
        """Write conversation to markdown file with YAML frontmatter."""
        with file_path.open("w", encoding="utf-8") as file:
            file.write("---\n")
            yaml.dump(metadata, file, sort_keys=False)
            file.write("---\n")
            conversation_url = self.get_conversation_url_prefix() + metadata["id"]
            file.write(f"[Conversation url]({conversation_url})\n")
            file.write("\n====================\n\n")

            for message in messages:
                file.write(f"# **{message['author']}**\n\n")
                urls = message["urls"]
                if urls:
                    file.write(f"{self.clean_text(message['text'])}\n\n")
                    file.write("Reference:\n")
                    urls.sort(key=lambda t: t[0])
                    for index, item in urls:
                        file.write(f"({index}) {item}\n")
                else:
                    file.write(f"{message['text']}\n\n")
                file.write("\n====================\n\n")
            print(f"File created: {file_path}")

    def update_file(self, conversation: dict, output_dir: Path) -> None:
        """Update or create a conversation file."""
        output_dir.mkdir(parents=True, exist_ok=True)
        messages = self.get_conversation_messages(conversation)
        data = self.conversation_info(conversation, messages)

        if not data["id"]:
            return

        existing_file = find_files_by_id(output_dir, data["id"])

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
                self.write_to_file(metadata, messages, existing_file)
        else:
            file_name = self.create_file_name_tile_and_id(data["original_title"], data["id"])
            file_path: Path = output_dir / file_name
            data["delete"] = False
            self.write_to_file(data, messages, file_path)

    def update_all_files(self, conversations, output_dir: Path) -> None:
        """Process all conversations and write to output directory."""
        for conversation in conversations:
            self.update_file(conversation, output_dir)
