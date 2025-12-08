from pathlib import Path
from export.chatgpt_converter import update_all_files as update_chatgpt
from export.grok_converter import update_all_files as update_grok
import argparse
import json

"""
CLI entry point for converting conversation exports into Markdown notes.

Supported providers:
    - ChatGPT (default)
    - Grok (xAI)

Run at the root folder:
    source venv/bin/activate
    python -m export.main /path/to/export.json /path/to/output_directory --provider "grok"

"""


def main():
    parser = argparse.ArgumentParser(
        description="Process conversation exports from supported providers into Obsidian-friendly markdown files.")
    parser.add_argument("input_file", type=Path, help="Path to the input conversations JSON file.")
    parser.add_argument("output_dir", type=Path, help="Directory to save the output files.")
    parser.add_argument(
        "--provider",
        choices=("chatgpt", "grok"),
        default="chatgpt",
        help="Conversation export provider to convert (default: chatgpt).",
    )
    args = parser.parse_args()
    if not args.input_file.exists():
        print(f"Error: The input file '{args.input_file}' does not exist.")
        return
    with args.input_file.open("r", encoding="utf-8") as file:
        conversations_data = json.load(file)
    converters = {
        "chatgpt": update_chatgpt,
        "grok": update_grok,
    }
    converters[args.provider](conversations_data, args.output_dir)


if __name__ == "__main__":
    main()
