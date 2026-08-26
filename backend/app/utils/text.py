import re
import unicodedata


def slugify(value: str) -> str:
    """Convert a string to a lowercase URL-friendly slug."""
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_value.lower())
    return slug.strip("-")
