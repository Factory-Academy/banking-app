import re


def slugify(value: str) -> str:
    """Convert text into a URL-friendly slug."""
    normalized = value.strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    return normalized.strip("-")
