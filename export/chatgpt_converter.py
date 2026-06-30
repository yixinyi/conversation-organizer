import re
import json
import string
from pathlib import Path

from export.base_converter import BaseConversationExporter
from export.utils import convert_latex_delimiters_excluding_backticks


# -------------------------------------------------------------------------
# ChatGPT Converter Implementation
# -------------------------------------------------------------------------

class ChatGPTConverter(BaseConversationExporter):
    """Exporter for ChatGPT conversations."""

    def get_conversation_url_prefix(self) -> str:
        return "https://chatgpt.com/c/"

    def clean_text(self, text):
        cleaned_text = "".join(char for char in text if char in string.printable)
        return re.sub(r"citeturn0search(\d+)", r"(See ref \1)", cleaned_text)

    def extract_message_parts(self, message: dict) -> list:
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

    def get_author_name(self, message: dict) -> str:
        author = message.get("author", {}).get("role", "")
        if author == "assistant":
            meta = message.get("metadata", {})
            model_slug = meta.get("model_slug")
            return model_slug
        elif author == "system":
            return "Custom user info"
        return author

    def extract_urls_from_message(self, message: dict) -> list:
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

    def get_conversation_messages(self, conversation: dict) -> list:
        messages = []
        current_node = conversation.get("current_node")
        mapping = conversation.get("mapping", {})
        while current_node:
            node = mapping.get(current_node, {})
            message = node.get("message") if node else None
            if message:
                parts = self.extract_message_parts(message)
                author = self.get_author_name(message)
                urls = self.extract_urls_from_message(message)
                if author != "tool":
                    # Exclude system messages unless explicitly marked
                    if parts and len(parts[0]) > 0:
                        if author != "system" or message.get("metadata", {}).get("is_user_system_message"):
                            messages.append({"author": author, "text": parts[0], "urls": urls})
            current_node = node.get("parent") if node else None
        return messages[::-1]

    def _extract_update_time(self, conversation: dict):
        """Override to use 'update_time' instead of 'modify_time'."""
        return conversation.get("update_time")


# -------------------------------------------------------------------------
# Module-level convenience functions for backward compatibility
# -------------------------------------------------------------------------

_converter = ChatGPTConverter()


def create_file_name_id(conversation_id: str) -> str:
    """Backward compatibility wrapper."""
    return f"{conversation_id}.md"


def update_all_files(conversations: list, output_dir: Path) -> None:
    """Backward compatibility wrapper."""
    _converter.update_all_files(conversations, output_dir)
