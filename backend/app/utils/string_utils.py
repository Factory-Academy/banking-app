import re
import unicodedata

def slugify(text: str, lowercase: bool = True) -> str:
    \"\"\"
    Convert a string to a URL-friendly slug.
    
    Args:
        text: String to slugify
        lowercase: Whether to convert result to lowercase (default: True)
    
    Returns:
        A slugified string containing only alphanumeric characters and hyphens.
    \"\"\"
    if not text:
        return ""
    
    # Normalize unicode characters
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    
    if lowercase:
        text = text.lower()
    
    # Replace non-alphanumeric characters with hyphens
    text = re.sub(r'[^a-z0-9]+' if lowercase else r'[^a-zA-Z0-9]+', '-', text)
    
    # Remove leading/trailing hyphens
    return text.strip('-')
