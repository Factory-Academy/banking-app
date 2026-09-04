import re


def slugify(value: str) -> str:
    """Convert a string into a URL-friendly slug."""
    normalized = value.strip().lower()
    normalized = re.sub(r"[^a-z0-9\s-]", "", normalized)
    normalized = re.sub(r"[\s_-]+", "-", normalized)
    return normalized.strip("-")
