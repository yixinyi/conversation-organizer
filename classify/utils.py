from pathlib import Path


def update_yaml_front_matter(file_path: Path, new_tags: list[str]):
    with file_path.open("r", encoding="utf-8") as f:
        content = f.read()

    if not content.startswith('---'):
        print(f"No YAML found in {file_path.name}, skipping.")
        return

    parts = content.split('---', 2)
    yaml_raw = parts[1]
    body = parts[2] if len(parts) > 2 else ""

    yaml_lines = yaml_raw.strip().splitlines()
    new_yaml_lines = []
    tags = []
    tags_found = False
    collecting_tags = False

    for line in yaml_lines:
        if line.strip().startswith("tags:"):
            tags_found = True
            collecting_tags = True
            continue  # skip 'tags:' line
        elif collecting_tags:
            if line.strip().startswith("-"):
                tags.append(line.strip().lstrip("- ").strip())
                continue
            else:
                collecting_tags = False  # end of tag list
        new_yaml_lines.append(line)

    # Add new tags, deduplicated and sorted
    all_tags = sorted(set(tags + new_tags))
    new_yaml_lines.append("tags:")
    new_yaml_lines.extend([f" - {tag}" for tag in all_tags])

    new_yaml_block = "---\n" + "\n".join(new_yaml_lines) + "\n---"
    updated_content = new_yaml_block + body

    with file_path.open("w", encoding="utf-8") as f:
        f.write(updated_content)



def update_yaml_front_matter2(file_path: Path, new_tag: str):
    with file_path.open("r", encoding="utf-8") as f:
        content = f.read()

    if not content.startswith('---'):
        print(f"No YAML found in {file_path.name}, skipping.")
        return

    parts = content.split('---', 2)
    yaml_raw = parts[1]
    body = parts[2] if len(parts) > 2 else ""

    yaml_lines = yaml_raw.strip().splitlines()
    new_yaml_lines = []
    tags = []
    tags_found = False

    for line in yaml_lines:
        if line.strip().startswith("tags:"):
            tags_found = True
            continue  # skip this line, we'll rebuild it
        elif tags_found and line.strip().startswith("-"):
            tags.append(line.strip().lstrip("- ").strip())
        else:
            new_yaml_lines.append(line)

    if new_tag not in tags:
        tags.append(new_tag)

    tags = sorted(set(tags))
    new_yaml_lines.append("tags:")
    new_yaml_lines.extend([f" - {tag}" for tag in tags])

    new_yaml_block = "---\n" + "\n".join(new_yaml_lines) + "\n---\n"
    updated_content = new_yaml_block + body

    with file_path.open("w", encoding="utf-8") as f:
        f.write(updated_content)
