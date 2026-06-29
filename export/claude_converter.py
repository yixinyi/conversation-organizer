from pathlib import Path

from export.base_converter import BaseConversationExporter


# -------------------------------------------------------------------------
# Claude Converter Implementation
# -------------------------------------------------------------------------

class ClaudeConverter(BaseConversationExporter):
    """Exporter for Claude conversations."""

    def get_conversation_url_prefix(self) -> str:
        return "https://claude.ai/chat/"

    def extract_message_parts(self, message: dict) -> list:
        """
        Extract text content from a Claude message.
        Uses the top-level 'text' field, or falls back to content[0].text.
        """
        text = message.get("text", "")
        if not text:
            content = message.get("content", [])
            if content and isinstance(content, list) and len(content) > 0:
                text = content[0].get("text", "")
        if not text:
            return []
        return [text]

    def get_author_name(self, message: dict) -> str:
        sender = message.get("sender", "")
        if sender == "human":
            return "User"
        return "Claude"

    def get_conversation_messages(self, conversation: dict) -> list:
        messages = []
        raw_messages = conversation.get("chat_messages", [])

        for item in raw_messages:
            parts = self.extract_message_parts(item)
            author = self.get_author_name(item)

            if parts and len(parts[0]) > 0:
                messages.append({
                    "author": author,
                    "text": parts[0],
                    "urls": []
                })
        return messages

    def _extract_conversation_id(self, conversation: dict) -> str:
        """Override to extract UUID from Claude format."""
        return conversation.get("uuid", "")

    def _extract_conversation_title(self, conversation: dict) -> str:
        """Override to extract name from Claude format."""
        return conversation.get("name", "Untitled Chat")

    def _extract_create_time(self, conversation: dict):
        """Override to extract create time from Claude format."""
        return conversation.get("created_at")

    def _extract_update_time(self, conversation: dict):
        """Override to extract update time from Claude format."""
        return conversation.get("updated_at")

    def _extract_is_archived(self, conversation: dict) -> bool:
        """Override to extract archived flag from Claude format."""
        return conversation.get("is_archived", False)


# -------------------------------------------------------------------------
# Module-level convenience functions for backward compatibility
# -------------------------------------------------------------------------

_converter = ClaudeConverter()


def update_all_files(conversations: list, output_dir: Path) -> None:
    """Backward compatibility wrapper."""
    _converter.update_all_files(conversations, output_dir)