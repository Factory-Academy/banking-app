"""Text manipulation utilities."""

import re
import unicodedata


def slugify(text: str, max_length: int = 100, separator: str = "-") -> str:
    """Convert a string to a URL-friendly slug.
    
    Converts text to lowercase, removes special characters, and replaces
    spaces with the specified separator. Useful for generating clean URLs
    from user-provided text.
    
    Args:
        text: The input string to slugify
        max_length: Maximum length of the resulting slug (default: 100)
        separator: Character to use as word separator (default: "-")
        
    Returns:
        A URL-friendly slug string
        
    Example:
        >>> slugify("Hello World!")
        'hello-world'
        >>> slugify("  Python 3.10  is Great!  ")
        'python-3-10-is-great'
        >>> slugify("Café & Restaurant", separator="_")
        'cafe_restaurant'
    """
    if not text:
        return ""
    
    # Normalize unicode characters (e.g., café -> cafe)
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    
    # Convert to lowercase
    text = text.lower()
    
    # Replace whitespace and underscores with separator
    text = re.sub(r"[\s_]+", separator, text)
    
    # Remove non-alphanumeric characters (except separator and hyphens)
    pattern = f"[^a-z0-9{re.escape(separator)}-]+"
    text = re.sub(pattern, "", text)
    
    # Remove duplicate separators
    text = re.sub(f"{re.escape(separator)}{{2,}}", separator, text)
    
    # Trim separators from start and end
    text = text.strip(separator)
    
    # Truncate to max length
    if len(text) > max_length:
        text = text[:max_length].rstrip(separator)
    
    return text
