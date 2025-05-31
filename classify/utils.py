import json
import re
import yaml
from typing import Optional, List


def extract_json_from_md(md_text: str):
    # Extract JSON code block using regex
    match = re.search(r'```json\s*(\{.*?\})\s*```', md_text, re.DOTALL)
    if match:
        json_str = match.group(1)
        data = json.loads(json_str)
        return data
    else:
        print("No valid JSON found.")


def add_metadata_to_md(md: str, title: Optional[str], tags: Optional[List[str]]):
    """
    Adds or updates YAML front matter, appends to 'aliases' and 'tags' in a Markdown string.
    The title is added as the MD title, and as an alias.

    Args:
        md: The Markdown content.
        title: Optional title to set.
        tags: Optional list of tags to append.

    Returns:
        The modified Markdown content with updated YAML front matter.
    """
    yaml_pattern = r'^---\n(.*?)\n---\n(.*)$'  # Front matter followed by body
    match = re.match(yaml_pattern, md, re.DOTALL)

    if match:
        front_matter = yaml.safe_load(match.group(1)) or {}
        body = match.group(2)
    else:
        front_matter = {}
        body = md.lstrip()

    def update_field(field: str, value: list):
        existing = front_matter.get(field, [])
        if not isinstance(existing, list):
            existing = [existing]
        combined = list(dict.fromkeys(existing + value))  # remove duplicates, preserve order
        front_matter[field] = combined

    if title is not None:
        update_field("aliases", [title])

    if tags is not None:
        update_field("tags", tags)

    new_yaml = yaml.dump(front_matter, sort_keys=False).strip()
    new_md = f"---\n{new_yaml}\n---\n# {title} \n\n{body}"
    return new_md
