import re

def clean_text(text):
    """
    Cleans raw text by removing extra whitespace, newlines,
    and other common artifacts.
    """
    text = text.replace('\n', ' ')           # Remove newlines
    text = re.sub(r'\s+', ' ', text)         # Replace multiple spaces with one
    text = text.strip()                      # Remove leading/trailing spaces
    return text