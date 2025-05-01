from pathlib import Path
import os
import json
from gemini import Gemini
from utils import update_yaml_front_matter
import ast

# Get the directory where the script is located
script_path = os.path.abspath(__file__)

script_dir = os.path.dirname(script_path)
root_dir = os.path.dirname(script_dir)

# Load config.json using the absolute path
config_path = os.path.join(root_dir, 'data', 'config.json')


with open(config_path, "r") as f:
    config = json.load(f)

api_key = config["api_key"]
api_url = config["api_url"]

tags = ["recipe", "health", "gardening", "house-improvement", "ai", "physics", "programming",
        "bureaucracy", "job-search", "finance", "math"]


def classify_files(folder_path: Path, llm):
    for file in folder_path.glob("*.md"):
        with file.open("r", encoding="utf-8") as f:
            content = f.read()

        if not content.startswith('---'):
            print(f"Skipping {file.name}: No YAML header.")
            continue

        conversation_text = content.split('---')[-1].strip()
        prompt = (
            f"Classify the following conversation into one or more of the following categories: {', '.join(tags)}.\n"
            "Feel free to add one or two new tags if appropriate. Be conservative though."
            f"Conversation: \n{conversation_text}\n"
            "Return only in the form of a Python list (not actual Python code)"
            " with the category names, i.e. ['cat1', 'cat2',...] "
        )
        response = llm.classify_conversation(prompt)
        if not response:
            print(f"Skipping {file.name}: No valid result returned.")
            continue
        result = ast.literal_eval(response)
        print(f"Classifying '{file.name}' as '{result}'...")
        update_yaml_front_matter(file, result)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Classify existing markdown conversations using gemini.")
    parser.add_argument("folder_path", type=Path, help="Folder containing markdown files to classify.")
    args = parser.parse_args()
    llm = Gemini(api_key, api_url)
    classify_files(args.folder_path, llm)
