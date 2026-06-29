from pathlib import Path

from export.base_converter import BaseConversationExporter


# -------------------------------------------------------------------------
# DeepSeek Converter Implementation
# -------------------------------------------------------------------------

class DeepSeekConverter(BaseConversationExporter):
    """Exporter for DeepSeek conversations."""

    def get_conversation_url_prefix(self) -> str:
        return "https://chat.deepseek.com/a/chats/s/"

    def extract_message_parts(self, message: dict) -> list:
        """
        Extract text content from a DeepSeek message.
        Returns a list of dicts with 'type' and 'content' keys,
        one per fragment (e.g. THINK, RESPONSE).
        """
        fragments = message.get("fragments", [])
        if not fragments:
            return []
        parts = []
        for fragment in fragments:
            content = fragment.get("content", "")
            if content:
                parts.append({
                    "type": fragment.get("type", ""),
                    "content": content
                })
        return parts

    def get_author_name(self, message: dict) -> str:
        """
        Determine author from fragment type.
        REQUEST -> "User"
        THINK / RESPONSE -> model name (e.g. "deepseek-reasoner") or "DeepSeek"
        """
        fragments = message.get("fragments", [])
        if fragments:
            msg_type = fragments[0].get("type", "")
            if msg_type == "REQUEST":
                return "User"
            elif msg_type in ("THINK", "RESPONSE"):
                return message.get("model", "DeepSeek")
        return "DeepSeek"

    def get_conversation_messages(self, conversation: dict) -> list:
        messages = []
        mapping = conversation.get("mapping", {})

        # Find the root node and walk the tree
        root_node = mapping.get("root")
        if not root_node:
            return messages

        # Walk children breadth-first from root
        current_ids = root_node.get("children", [])
        while current_ids:
            next_ids = []
            for node_id in current_ids:
                node = mapping.get(node_id, {})
                message = node.get("message")
                if message:
                    parts = self.extract_message_parts(message)
                    author = self.get_author_name(message)
                    if not parts:
                        continue

                    # Separate REQUEST from model fragments
                    request_parts = [p for p in parts if p["type"] == "REQUEST"]
                    model_parts = [p for p in parts if p["type"] in ("THINK", "RESPONSE")]

                    # Add user messages
                    for part in request_parts:
                        messages.append({
                            "author": "User",
                            "text": part["content"],
                            "urls": []
                        })

                    # Add model messages — combine THINK + RESPONSE into one entry
                    if model_parts:
                        if len(model_parts) == 1:
                            text = model_parts[0]["content"]
                        else:
                            # Combine multiple fragments with subheadings
                            sub_sections = []
                            for part in model_parts:
                                sub_sections.append(f"**{part['type']}**\n{part['content']}")
                            text = "\n\n".join(sub_sections)

                        messages.append({
                            "author": author,
                            "text": text,
                            "urls": []
                        })

                children = node.get("children", [])
                next_ids.extend(children)
            current_ids = next_ids

        return messages

    def _extract_conversation_id(self, conversation: dict) -> str:
        """Override to extract ID from DeepSeek format."""
        return conversation.get("id", "")

    def _extract_conversation_title(self, conversation: dict) -> str:
        """Override to extract title from DeepSeek format."""
        return conversation.get("title", "Untitled Chat")

    def _extract_create_time(self, conversation: dict):
        """Override to extract create time from DeepSeek format."""
        return conversation.get("inserted_at")

    def _extract_update_time(self, conversation: dict):
        """Override to extract update time from DeepSeek format."""
        return conversation.get("updated_at")

    def _extract_is_archived(self, conversation: dict) -> bool:
        """Override to extract archived flag from DeepSeek format."""
        return conversation.get("is_archived", False)


# -------------------------------------------------------------------------
# Module-level convenience functions for backward compatibility
# -------------------------------------------------------------------------

_converter = DeepSeekConverter()


def update_all_files(conversations: list, output_dir: Path) -> None:
    """Backward compatibility wrapper."""
    _converter.update_all_files(conversations, output_dir)