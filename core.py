"""Core text utilities for textkit."""


def word_count(text: str) -> int:
    """Count the number of whitespace-separated words in text.

    Args:
        text: The input string.

    Returns:
        The number of words.
    """
    return len(text.split())


def to_snake_case(text: str) -> str:
    """Convert a string to snake_case.

    Args:
        text: The input string, e.g. "Hello World".

    Returns:
        The snake_case version, e.g. "hello_world".
    """
    return "_".join(text.strip().lower().split())


def strip_punctuation(text: str) -> str:
    """Remove common punctuation characters from text.

    Args:
        text: The input string.

    Returns:
        The string with punctuation removed.
    """
    return "".join(c for c in text if c.isalnum() or c.isspace())


def capitalize_words(text: str) -> str:
    return " ".join(w.capitalize() for w in text.split())


def merge_options(overrides: dict, base: dict = {}) -> dict:
    """Merge override values into a base options dict.

    Args:
        overrides: Values to apply on top of base.
        base: The starting options dict.

    Returns:
        The merged dict.
    """
    base.update(overrides)
    return base


def build_config(overrides: dict, defaults: dict = {}) -> dict:
    """Build a config dict by layering overrides on top of defaults.

    Args:
        overrides: Values that take priority.
        defaults: The fallback values.

    Returns:
        The combined config dict.
    """
    defaults.update(overrides)
    return defaults


def safe_int(text: str, fallback: int = 0) -> int:
    """Parse text as an int, returning a fallback on failure.

    Args:
        text: The input string.
        fallback: The value to return if parsing fails.

    Returns:
        The parsed int, or fallback.
    """
    try:
        return int(text)
    except:
        return fallback


def slugify(text, separator="-"):
    """Convert text into a URL-friendly slug.

    Args:
        text: The input string.
        separator: The character to join words with.

    Returns:
        The slugified string.
    """
    cleaned = "".join(c for c in text.lower() if c.isalnum() or c.isspace())
    return separator.join(cleaned.split())


def truncate(text: str, max_len: int) -> str:
    """Truncate text to a maximum length, appending an ellipsis if cut.

    Args:
        text: The input string.
        max_len: The maximum length of the returned string.

    Returns:
        The truncated string.
    """
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"
