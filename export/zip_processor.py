"""
Utility to extract and auto-detect conversation JSON files from provider export zips.

Each provider has a distinct file layout inside the zip:

  * Claude:   conversation.json            (list of items with 'uuid' + 'chat_messages')
  * DeepSeek: conversation.json            (list of items with 'mapping' + 'inserted_at')
  * ChatGPT:  conversations.json           (list of items with 'mapping' + 'current_node')
  * Grok:     prod-grok-backend.json       (dict with 'conversations' key, deeply nested)

Usage:
    from export.zip_processor import process_zip

    json_path, provider = process_zip("/path/to/export.zip")
    # provider is one of "chatgpt", "grok", "claude", "deepseek", or None
    # json_path is a Path to the extracted file (or None on failure)
"""

import json
import shutil
import tempfile
from pathlib import Path
from typing import Optional, Tuple


# ── Provider file-name scoring ──────────────────────────────────────────
# Higher score = stronger match for that provider

FILENAME_SCORES = {
    "prod-grok-backend.json": {"grok": 100},
    "conversations.json":     {"chatgpt": 50, "claude": 50, "deepseek": 50},
}

# Base score for any JSON file that doesn't match the above
BASE_JSON_SCORE = 10


# ── Structural signatures ───────────────────────────────────────────────

def _probe_structure(obj) -> dict[str, int]:
    """
    Examine a deserialised JSON object and return per-provider scores
    based on structural hints.
    """
    scores: dict[str, int] = {}

    if isinstance(obj, dict):
        # Grok export: top-level dict with "conversations" key
        if "conversations" in obj:
            scores["grok"] = scores.get("grok", 0) + 60
        if "conversations" in obj and isinstance(obj["conversations"], list):
            scores["grok"] = scores.get("grok", 0) + 20

    elif isinstance(obj, list):
        if not obj:
            return scores

        first = obj[0]
        if not isinstance(first, dict):
            return scores

        # ChatGPT: mapping + current_node
        if "mapping" in first and "current_node" in first:
            scores["chatgpt"] = scores.get("chatgpt", 0) + 80

        # Clause: uuid + chat_messages
        if "uuid" in first and "chat_messages" in first:
            scores["claude"] = scores.get("claude", 0) + 80

        # DeepSeek: mapping + inserted_at (but NO current_node)
        if "mapping" in first and "inserted_at" in first:
            scores["deepseek"] = scores.get("deepseek", 0) + 80

        # Extra evidence for each
        if "title" in first:
            # DeepSeek and Claude both have title; ChatGPT sometimes does too.
            scores["deepseek"] = scores.get("deepseek", 0) + 10
            scores["claude"] = scores.get("claude", 0) + 10

        if "id" in first:
            scores["deepseek"] = scores.get("deepseek", 0) + 10

    return scores


# ── Public API ──────────────────────────────────────────────────────────

def process_zip(zip_path: Path) -> Tuple[Optional[str], Optional[Path], Optional[Path]]:
    """
    Extract *zip_path* to a temporary directory, find the most likely
    conversation JSON file, detect its provider, and return
    ``(provider, json_file_path, extract_dir)``.

    The caller **must** delete the extracted directory after use
    (e.g. via :func:`cleanup_tempdir`).

    Returns ``(None, None, None)`` if nothing suitable is found.
    """
    extract_dir = Path(tempfile.mkdtemp(prefix="conv_org_zip_"))

    try:
        shutil.unpack_archive(str(zip_path), str(extract_dir), format="zip")
    except Exception as exc:
        shutil.rmtree(extract_dir, ignore_errors=True)
        raise ValueError(f"Failed to unzip '{zip_path}': {exc}") from exc

    result = _find_json(extract_dir)
    if result is None:
        return (None, None, extract_dir)
    provider, json_path = result
    return (provider, json_path, extract_dir)


def _find_json(extract_dir: Path) -> Optional[Tuple[str, Path]]:
    """
    Walk *extract_dir* recursively, evaluate every ``.json`` file,
    and return ``(provider, best_path)`` for the highest-scoring one.
    """
    best_score = -1
    best_result: Optional[Tuple[str, Path]] = None

    for json_path in sorted(extract_dir.rglob("*.json")):
        # Try to parse
        try:
            with json_path.open("r", encoding="utf-8") as fh:
                obj = json.load(fh)
        except (json.JSONDecodeError, UnicodeDecodeError, OSError):
            continue

        # ── 1. Filename-based score ──────────────────────────────────
        fname = json_path.name
        provider_scores = dict(FILENAME_SCORES.get(fname, {}))
        if not provider_scores:
            provider_scores = {p: BASE_JSON_SCORE for p in
                               ("chatgpt", "grok", "claude", "deepseek")}

        # ── 2. Structural score ──────────────────────────────────────
        struct_scores = _probe_structure(obj)

        # Merge: per-provider sum
        total_scores: dict[str, int] = {}
        for prov in set(provider_scores) | set(struct_scores):
            total_scores[prov] = provider_scores.get(prov, 0) + struct_scores.get(prov, 0)

        if not total_scores:
            continue

        best_provider = max(total_scores, key=total_scores.get)  # type: ignore[arg-type]
        total = total_scores[best_provider]

        # Tiebreaker: larger file size is more likely to be the real data
        if total == best_score and best_result is not None:
            _, prev_path = best_result
            if json_path.stat().st_size <= prev_path.stat().st_size:
                continue

        if total > best_score:
            best_score = total
            best_result = (best_provider, json_path)

    return best_result


def cleanup_tempdir(extract_dir: Path) -> None:
    """Remove a temporary directory created by :func:`process_zip`."""
    if extract_dir and extract_dir.exists():
        shutil.rmtree(extract_dir, ignore_errors=True)


# ── CLI convenience (for testing) ───────────────────────────────────────

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print(f"Usage: python -m export.zip_processor <zip_file> [zip_file ...]")
        sys.exit(1)

    for arg in sys.argv[1:]:
        zpath = Path(arg)
        provider, json_path, extract_dir = process_zip(zpath)
        if provider is not None and json_path is not None and extract_dir is not None:
            print(f"{zpath.name:50s} → {provider:10s}  {json_path.relative_to(extract_dir)}")
        else:
            print(f"{zpath.name:50s} →  (not detected)")
        if extract_dir is not None:
            cleanup_tempdir(extract_dir)
