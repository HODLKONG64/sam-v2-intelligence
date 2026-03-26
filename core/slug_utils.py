import re


def is_valid_slug(slug: str) -> bool:
    """Slug must be lowercase, hyphen-separated, no sam- prefix."""
    if slug.startswith("sam-"):
        return False
    return bool(re.match(r'^[a-z0-9][a-z0-9\-]*[a-z0-9]$', slug))


def make_slug(name: str) -> str:
    """Convert an entity name to a valid slug (lowercase, hyphen-separated)."""
    slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
    return slug
