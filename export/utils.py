import re
import string
import unicodedata
from datetime import datetime

from datetime import datetime
from typing import Union


def format_timestamp(time_input: Union[str, int, float, None]) -> str:
    """
    Standardizes timestamps from various sources into a clean ISO string.

    Handles:
    1. Unix Timestamp (int/float): ChatGPT (e.g., 1678912345)
    2. ISO String (str): Grok (e.g., "2025-11-11T17:29:34.123Z")

    Returns:
    "2025-11-11T17:29:34" (No microseconds, no +00:00 offset)
    """
    if not time_input:
        # Fallback to now if data is missing
        return datetime.now().isoformat(timespec="seconds")

    dt_object = None

    try:
        # CASE 1: Unix Timestamp (ChatGPT)
        if isinstance(time_input, (int, float)):
            # fromtimestamp converts to Local Time
            dt_object = datetime.fromtimestamp(time_input)

        # CASE 2: ISO String (Grok)
        elif isinstance(time_input, str):
            # Replace Z to ensure compatibility with Python < 3.11
            clean_str = time_input.replace("Z", "+00:00")
            dt_object = datetime.fromisoformat(clean_str)

    except (ValueError, OSError):
        # If parsing fails, return current time or empty string
        return datetime.now().isoformat(timespec="seconds")

    if dt_object:
        # 1. Remove Timezone info (+00:00) using replace(tzinfo=None)
        # 2. Remove microseconds using timespec="seconds"
        return dt_object.replace(tzinfo=None).isoformat(timespec="seconds")

    return str(time_input)

def convert_latex_delimiters_excluding_backticks(text):
    """
    Converts LaTeX inline and display math delimiters, but excludes
    any matches that are found within backticks (`...`).
    """

    # Regex patterns for math delimiters
    inline_math_pattern = r'\\\(\s*(.*?)\s*\\\)'
    display_math_pattern = r'\\\[\s*(.*?)\s*\\\]'

    # Combined pattern:
    # 1. `([^`]*?)`   : Matches any content within backticks (captures the content).
    #                    The `[^`]*?` ensures it's non-greedy and doesn't cross backticks.
    # 2. |             : OR
    # 3. (inline_math_pattern) : Matches the inline math pattern (captures the whole pattern).
    # 4. |             : OR
    # 5. (display_math_pattern): Matches the display math pattern (captures the whole pattern).
    # Using re.DOTALL allows `.` to match newlines, important for multiline display math.
    combined_pattern = rf"`([^`]*?)`|({inline_math_pattern})|({display_math_pattern})"

    def replacer(match):
        # Group 1: Content inside backticks
        if match.group(1) is not None:
            return f"`{match.group(1)}`"  # Return the whole backtick block unchanged

        # Group 2: Full inline math match (e.g., '\(x^2\)')
        # Group 3: Content inside inline math (e.g., 'x^2')
        elif match.group(2) is not None:
            return f"${match.group(3)}$"  # Convert inline math

        # Group 4: Full display math match (e.g., '\[E=mc^2\]')
        # Group 5: Content inside display math (e.g., 'E=mc^2')
        elif match.group(4) is not None:
            return f"$${match.group(5)}$$"  # Convert display math

        # This case shouldn't be reached if the patterns are mutually exclusive and comprehensive
        return match.group(0)  # Fallback: return the full match unchanged

    return re.sub(combined_pattern, replacer, text, flags=re.DOTALL)


def sanitize_title(title):
    title = unicodedata.normalize("NFKC", title)
    title = re.sub(r'[<>:"/\\|?*\x00-\x1F\s]', '_', title)
    # Strip leading/trailing spaces
    title = title.strip()
    # Remove trailing period (just one, if present)
    title = title.strip('.')
    return title[:140]



