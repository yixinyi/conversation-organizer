from pathlib import Path
from utils import extract_json_from_md, add_metadata_to_md


def process_conversation(file, llm, tags_with_descriptions):
    with file.open("r", encoding="utf-8") as f:
        content = f.read()

    conversation_text = content.split('---')[-1].strip()
    prompt = (
        "Read the conversation below. "
        f"Keep in mind this dictionary where keys are tags and values are their description: \n{tags_with_descriptions}\n"
        f"Now, think of a good title and choose the most fitting tags. "
        "Feel free to add a few more tags if appropriate, but not too redundant or too specific (be conservative). "
        "If the tag has several words, make sure to connect them with a hyphen. "
        "Return in the format of a json with two fields 'title' and 'tags'. "
        f"Conversation: \n{conversation_text}\n"
    )
    data = extract_json_from_md(llm.classify_conversation(prompt))
    title = data["title"]
    tags = data["tags"]
    with file.open("w", encoding="utf-8") as f:
        f.write(add_metadata_to_md(content, title, tags))

    print(f"The title is '{title}' and tags '{tags}'.")


def process_all_files(folder_path: Path, llm, tags_with_descriptions):
    for file in folder_path.glob("*.md"):
        process_conversation(file, llm, tags_with_descriptions)


