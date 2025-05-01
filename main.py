from pathlib import Path
from export.converter import process_conversations
from classify.ollama_mistral import classify_files
import argparse
import json

def main():
    parser = argparse.ArgumentParser(
        description="Process conversation data from a JSON file and create Obsidian-friendly markdown files.")
    parser.add_argument("input_file", type=Path, help="Path to the input conversations JSON file.")
    parser.add_argument("output_dir", type=Path, help="Directory to save the output files.")
    args = parser.parse_args()
    if not args.input_file.exists():
        print(f"Error: The input file '{args.input_file}' does not exist.")
        return
    with args.input_file.open("r", encoding="utf-8") as file:
        conversations_data = json.load(file)
    created_files_info = process_conversations(conversations_data, args.output_dir)
    for info in created_files_info:
        print(f"Created file: {info['file']}")

    # classify_files(args.output_dir)


if __name__ == "__main__":
    main()