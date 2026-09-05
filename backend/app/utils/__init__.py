import re


def slugify(value: str) -> str:
    """Convert text to a lowercase, URL-safe slug."""
    normalized = value.strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    return normalized.strip("-")

