import os
import json
from pathlib import Path
from classifier import process_all_files
from llm_models import Gemini, Ollama


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Process the existing markdown conversations using Gemini.")
    parser.add_argument("folder_path", type=Path, help="Folder containing markdown files to classify.")
    args = parser.parse_args()

    # Get the directory where the script is located
    script_path = os.path.abspath(__file__)
    script_dir = os.path.dirname(script_path)
    root_dir = os.path.dirname(script_dir)

    with open(os.path.join(root_dir, 'config', 'user_tags.json'), "r") as f:
        tag_dict = json.load(f)

    llm = Gemini()
    # llm = Ollama()
    # process_conversation(args.folder_path, llm, tag_dict) # for a single file
    process_all_files(args.folder_path, llm, tag_dict)  # for a folder


if __name__ == "__main__":
    main()
