import json
import re
from pathlib import Path

from export.base_converter import BaseConversationExporter
from export.utils import convert_latex_delimiters_excluding_backticks


# -------------------------------------------------------------------------
# Grok Converter Implementation
# -------------------------------------------------------------------------

class GrokConverter(BaseConversationExporter):
    """Exporter for Grok conversations."""

    def get_conversation_url_prefix(self) -> str:
        return "https://grok.com/c/"

    def _remove_grok_tags(self, text: str) -> str:
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

    def extract_message_parts(self, response_data: dict) -> list:
        content = response_data.get("message", "")
        if not content:
            return []

        # 1. Remove the XML/HTML-like Grok tags
        content = self._remove_grok_tags(content)

        # 2. Clean Latex delimiters
        text = convert_latex_delimiters_excluding_backticks(content)

        return [text]

    def get_author_name(self, response_data: dict) -> str:
        sender = response_data.get("sender")
        if sender == "human":
            return "User"
        # Fallback to model name (e.g. "grok-beta") or generic "Grok"
        return response_data.get("model", "Grok")

    def get_conversation_messages(self, conversation_wrapper: dict) -> list:
        messages = []
        # Assumes 'responses' list is chronologically sorted
        raw_responses = conversation_wrapper.get("responses", [])

        for item in raw_responses:
            data = item.get("response", {})
            parts = self.extract_message_parts(data)
            author = self.get_author_name(data)

            # Note: Grok inline citations are usually stripped by the regex above.
            # If Grok adds a metadata field for URLs later, we can extract them here.
            if parts and len(parts[0]) > 0:
                messages.append({
                    "author": author,
                    "text": parts[0],
                    "urls": []
                })
        return messages

    def _extract_conversation_id(self, conversation_wrapper: dict) -> str:
        """Override to extract ID from Grok format."""
        meta = conversation_wrapper.get("conversation", {})
        return meta.get("id", "")

    def _extract_conversation_title(self, conversation_wrapper: dict) -> str:
        """Override to extract title from Grok format."""
        meta = conversation_wrapper.get("conversation", {})
        return meta.get("title", "Untitled Chat")

    def _extract_create_time(self, conversation_wrapper: dict):
        """Override to extract create time from Grok format."""
        meta = conversation_wrapper.get("conversation", {})
        return meta.get("create_time")

    def _extract_update_time(self, conversation_wrapper: dict):
        """Override to extract update time from Grok format."""
        meta = conversation_wrapper.get("conversation", {})
        return meta.get("modify_time")

    def _extract_is_archived(self, conversation_wrapper: dict) -> bool:
        """Override to extract archived flag from Grok format."""
        meta = conversation_wrapper.get("conversation", {})
        return meta.get("starred", False)


# -------------------------------------------------------------------------
# Module-level convenience functions for backward compatibility
# -------------------------------------------------------------------------

_converter = GrokConverter()


def update_all_files(export_data: dict, output_dir: Path) -> None:
    """Backward compatibility wrapper."""
    conversations_list = export_data.get("conversations", [])
    _converter.update_all_files(conversations_list, output_dir)