import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, List, Tuple

import yaml

from common.utils import find_files_by_id, parse_file
from export.utils import convert_latex_delimiters_excluding_backticks, sanitize_title, clean_text


def _normalize_timestamp(value: Any) -> str:
    """Return a best-effort ISO timestamp string for Grok exports."""
    def _fallback() -> str:
        return datetime.now(timezone.utc).replace(tzinfo=None).isoformat(timespec="seconds")

    if value is None:
        return _fallback()
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value).isoformat(timespec="seconds")
    if isinstance(value, str):
        candidate = value.strip()
        if not candidate:
            return _fallback()
        if candidate.isdigit():
            return datetime.fromtimestamp(int(candidate)).isoformat(timespec="seconds")
        if candidate.endswith("Z"):
            candidate = candidate[:-1] + "+00:00"
        for fmt in (candidate, candidate.replace(" ", "T")):
            try:
                dt = datetime.fromisoformat(fmt)
                if dt.tzinfo is not None:
                    dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
                return dt.isoformat(timespec="seconds")
            except ValueError:
                continue
        try:
            return datetime.fromtimestamp(float(candidate)).isoformat(timespec="seconds")
        except (ValueError, TypeError):
            return _fallback()
    return _fallback()


def _conversation_id(conversation: dict) -> str:
    keys = (
        "id",
        "conversation_id",
        "conversationId",
        "chat_id",
        "chatId",
        "uuid",
        "thread_id",
        "threadId",
    )
    for key in keys:
        value = conversation.get(key)
        if value:
            return str(value)
    for message in conversation.get("messages", []):
        for key in keys:
            value = message.get(key)
            if value:
                return str(value)
    hashed = hashlib.sha1(json.dumps(conversation, default=str, sort_keys=True).encode("utf-8"))
    return hashed.hexdigest()


def _conversation_title(conversation: dict) -> str:
    for key in ("title", "chat_title", "name"):
        title = conversation.get(key)
        if title:
            return str(title)
    return "Grok conversation"


def _conversation_archive(conversation: dict) -> bool:
    for key in ("is_archived", "archived", "archivedAt", "deleted"):
        value = conversation.get(key)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in {"true", "1", "yes"}
    return False


def _extract_content_piece(piece: Any) -> str:
    if piece is None:
        return ""
    if isinstance(piece, str):
        return piece
    if isinstance(piece, dict):
        for key in ("text", "value", "content", "body"):
            value = piece.get(key)
            if isinstance(value, str):
                return value
        if piece.get("type") == "code":
            language = piece.get("language", "")
            code_content = piece.get("text") or piece.get("value") or ""
            fence = language or ""
            return f"```{fence}\n{code_content}\n```"
    if isinstance(piece, Iterable) and not isinstance(piece, (bytes, bytearray)):
        collected = []
        for item in piece:
            chunk = _extract_content_piece(item)
            if chunk:
                collected.append(chunk)
        return "\n\n".join(collected)
    return ""


def _message_text(message: dict) -> str:
    content = message.get("content")
    text = _extract_content_piece(content)
    if not text:
        attachments = message.get("attachments") or message.get("media")
        text = _extract_content_piece(attachments)
    if not text:
        text = message.get("text", "")
    return convert_latex_delimiters_excluding_backticks(text.strip()) if text else ""


def _message_author(message: dict) -> str:
    for key in ("role", "author", "sender", "speaker"):
        value = message.get(key)
        if isinstance(value, str):
            return value
        if isinstance(value, dict):
            for name_key in ("name", "username", "display_name", "role"):
                name = value.get(name_key)
                if name:
                    return str(name)
    return "assistant" if message.get("is_bot") else "user"


def _message_urls(message: dict) -> List[Tuple[int, str]]:
    urls: List[Tuple[int, str]] = []
    references = message.get("references") or message.get("citations")
    if isinstance(references, list):
        for index, entry in enumerate(references, start=1):
            if isinstance(entry, dict):
                url = entry.get("url") or entry.get("href")
            else:
                url = entry
            if url:
                urls.append((index, str(url)))
    return urls


def get_conversation_messages(conversation: dict) -> list:
    messages = []
    for message in conversation.get("messages", []):
        text = _message_text(message)
        if not text:
            continue
        author = _message_author(message)
        urls = _message_urls(message)
        messages.append({"author": author, "text": text, "urls": urls})
    return messages


def _conversation_url(conversation: dict, conversation_id: str) -> str:
    for key in ("url", "conversation_url", "link"):
        url = conversation.get(key)
        if url:
            return str(url)
    return f"https://grok.com/c/{conversation_id}"


def conversation_info(conversation: dict) -> dict:
    messages = get_conversation_messages(conversation)
    conversation_id = _conversation_id(conversation)
    create_time = None
    update_time = None
    for key in ("created_at", "create_time", "created", "createdAt"):
        if create_time:
            break
        create_time = conversation.get(key)
    for key in ("updated_at", "update_time", "modified_at", "last_modified", "updatedAt"):
        if update_time:
            break
        update_time = conversation.get(key)
    data = {
        "id": conversation_id,
        "create_time": _normalize_timestamp(create_time),
        "update_time": _normalize_timestamp(update_time or create_time),
        "original_title": _conversation_title(conversation),
        "turns": len(messages),
        "characters": sum(len(m["text"]) for m in messages),
        "archive": _conversation_archive(conversation),
        "url": _conversation_url(conversation, conversation_id),
    }
    return data


def create_file_name_tile_and_id(title: str, conversation_id: str) -> str:
    sanitized_title = sanitize_title(title)
    return f"{sanitized_title}[{conversation_id}].md"


def write_to_file(metadata: dict, messages: list, file_path: Path) -> None:
    with file_path.open("w", encoding="utf-8") as file:
        file.write("---\n")
        yaml.dump(metadata, file, sort_keys=False)
        file.write("---\n")
        conversation_url = metadata.get("url")
        if conversation_url:
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
    output_dir.mkdir(parents=True, exist_ok=True)
    data = conversation_info(conversation)
    existing_file = find_files_by_id(output_dir, data["id"])
    messages = get_conversation_messages(conversation)
    if existing_file is not None:
        metadata = parse_file(existing_file)["metadata"]
        new_update_time = datetime.fromisoformat(data["update_time"])
        old_update_raw = metadata.get("update_time")
        if isinstance(old_update_raw, str):
            old_update_time = datetime.fromisoformat(old_update_raw)
        else:
            old_update_time = old_update_raw
        if new_update_time > old_update_time:
            if "delete" in metadata:
                if metadata["delete"]:
                    metadata["delete_time"] = metadata["update_time"]
            else:
                metadata["delete"] = False
            metadata.update(data)
            write_to_file(metadata, messages, existing_file)
    else:
        file_name = create_file_name_tile_and_id(data["original_title"], data["id"])
        file_path = output_dir / file_name
        data["delete"] = False
        write_to_file(data, messages, file_path)


def _iter_conversations(export_data: Any) -> Iterable[dict]:
    if isinstance(export_data, list):
        for conversation in export_data:
            if isinstance(conversation, dict):
                yield conversation
        return
    if isinstance(export_data, dict):
        for key in ("conversations", "chats", "data", "threads"):
            value = export_data.get(key)
            if isinstance(value, list):
                for conversation in value:
                    if isinstance(conversation, dict):
                        yield conversation
                return
        for conversation in export_data.values():
            if isinstance(conversation, dict):
                yield conversation
        return
    raise TypeError("Unsupported Grok export format")


def update_all_files(export_data: Any, output_dir: Path) -> None:
    for conversation in _iter_conversations(export_data):
        update_file(conversation, output_dir)
