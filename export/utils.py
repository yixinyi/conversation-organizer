import re
import unicodedata


def convert_latex_to_markdown(text):
    """
    Convert LaTeX notation from \( ... \) to $...$ and \[ ... \] to $$ ... $$.
    """
    text = re.sub(r'\\\(\s*(.*?)\s*\\\)', r'$\1$', text)  # Inline math
    text = re.sub(r'\\\[\s*(.*?)\s*\\\]', r'$$\n\1\n$$', text, flags=re.DOTALL)  # Block math
    return text


def sanitize_title(title):
    title = unicodedata.normalize("NFKC", title)
    title = re.sub(r'[<>:"/\\|?*\x00-\x1F\s]', '_', title)
    # Strip leading/trailing spaces
    title = title.strip()
    # Remove trailing period (just one, if present)
    title = title.strip('.')
    return title[:140]

