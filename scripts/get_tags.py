import yaml
from pathlib import Path

# python scripts/get_tags.py path/to/md/file


def extract_tags_from_markdown(file_path: Path):
    with file_path.open("r", encoding="utf-8") as f:
        content = f.read()

    if not content.startswith('---'):
        print(f"No YAML header found in {file_path.name}.")
        return []

    parts = content.split('---', 2)
    if len(parts) < 3:
        print(f"Malformed YAML in {file_path.name}.")
        return []

    yaml_raw = parts[1]
    try:
        yaml_data = yaml.safe_load(yaml_raw)
    except yaml.YAMLError as e:
        print(f"YAML parsing error in {file_path.name}: {e}")
        return []

    tags = yaml_data.get('tags')
    if not isinstance(tags, list):
        print(f"No valid 'tags' list found in {file_path.name}.")
        return []

    return tags


# Example usage:
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", type=Path, help="Path to the input MD file.")
    args = parser.parse_args()

    tags = extract_tags_from_markdown(args.input_file)
    print(tags)

