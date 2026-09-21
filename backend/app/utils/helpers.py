"""Pure helper utility functions."""

import re


def slugify(text: str) -> str:
    """
    Convert a string to a URL-safe slug format.
    
    Converts to lowercase, replaces spaces with hyphens, and removes
    special characters while preserving alphanumeric characters and hyphens.
    
    Args:
        text: The string to convert to a slug.
    
    Returns:
        A slugified version of the input string.
    
    Example:
        >>> slugify("Whole Foods Market")
        'whole-foods-market'
        >>> slugify("Apple Store!")
        'apple-store'
    """
    # Convert to lowercase
    text = text.lower()
    
    # Replace spaces with hyphens
    text = re.sub(r'\s+', '-', text)
    
    # Remove special characters (keep alphanumeric and hyphens)
    text = re.sub(r'[^a-z0-9\-]', '', text)
    
    # Remove consecutive hyphens
    text = re.sub(r'-+', '-', text)
    
    # Strip leading/trailing hyphens
    text = text.strip('-')
    
    return text
