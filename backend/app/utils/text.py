import re


def slugify(value: str) -> str:
    """Convert text into a URL-friendly slug."""
    if value is None:
        return ""

    normalized = str(value).strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    return normalized.strip("-")
