import yaml
from pathlib import Path


def extract_tags_from_markdown(file_path: Path):
    with file_path.open("r", encoding="utf-8") as f:
        content = f.read()

    if not content.startswith('---'):
        return [], content

    parts = content.split('---', 2)
    if len(parts) < 3:
        return [], content

    yaml_raw = parts[1]
    body = parts[2]

    try:
        yaml_data = yaml.safe_load(yaml_raw)
    except yaml.YAMLError:
        return [], content

    tags = yaml_data.get('tags', [])
    if not isinstance(tags, list):
        return [], content

    return tags, (yaml_data, body)


def replace_tag_in_markdown(file_path: Path, old_tag: str, new_tag: str):
    tags, payload = extract_tags_from_markdown(file_path)

    if not tags:
        return False

    yaml_data, body = payload

    updated = False
    new_tags = []
    for tag in tags:
        if isinstance(tag, str) and tag == old_tag:  # case-sensitive match
            new_tags.append(new_tag)
            updated = True
        else:
            new_tags.append(tag)

    if not updated:
        return False

    yaml_data['tags'] = new_tags

    # No new lines are added after updating the tags
    new_yaml_block = "---\n" + yaml.dump(yaml_data, allow_unicode=True, sort_keys=False).strip() + "\n---"
    updated_content = new_yaml_block + ("\n" if not body.startswith("\n") else "") + body

    with file_path.open("w", encoding="utf-8") as f:
        f.write(updated_content)

    return True


def replace_tag_in_folder(folder_path: Path, old_tag: str, new_tag: str):
    md_files = list(folder_path.glob("*.md"))
    if not md_files:
        print(f"No markdown files found in {folder_path}")
        return

    for file in md_files:
        if replace_tag_in_markdown(file, old_tag, new_tag):
            print(f"Replaced '{old_tag}' with '{new_tag}' in {file.name}")
        else:
            print(f"No matching tag in {file.name}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Batch replace a tag with a new tag in markdown files.")
    parser.add_argument("folder_path", type=Path, help="Folder containing markdown files.")
    parser.add_argument("old_tag", type=str, help="Tag to replace (case-sensitive).")
    parser.add_argument("new_tag", type=str, help="New tag to insert.")
    args = parser.parse_args()

    replace_tag_in_folder(args.folder_path, args.old_tag, args.new_tag)
