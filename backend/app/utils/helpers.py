import re


def slugify(text: str) -> str:
    """
    Convert a string to a URL-friendly slug.
    
    Args:
        text: The input string to slugify
        
    Returns:
        A lowercase string with spaces and special characters replaced by hyphens
        
    Examples:
        >>> slugify("Hello World")
        'hello-world'
        >>> slugify("  Multiple   Spaces  ")
        'multiple-spaces'
        >>> slugify("Special@#Characters!")
        'special-characters'
    """
    # Convert to lowercase
    text = text.lower()
    
    # Replace any sequence of non-alphanumeric characters with a single hyphen
    text = re.sub(r'[^a-z0-9]+', '-', text)
    
    # Remove leading and trailing hyphens
    text = text.strip('-')
    
    return text
