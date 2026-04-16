"""Ingredient text parser — converts raw OCR text to structured ingredient list."""

import re

# Common prefixes to strip
_PREFIXES = [
    "配料表：", "配料表:", "配料：", "配料:",
    "原料：", "原料:", "成分：", "成分:",
    "原材料：", "原材料:",
]

# Separator pattern: Chinese comma, enumeration dot, regular comma, semicolons
_SEPARATOR_PATTERN = re.compile(r"[，、,；;]")


def parse_ingredients(text: str | None) -> list[str]:
    """Parse ingredient text into a list of individual ingredients.

    Handles various Chinese text formats and separators.
    """
    if not text:
        return []

    text = text.strip()
    if not text:
        return []

    # Strip known prefixes
    for prefix in _PREFIXES:
        if text.startswith(prefix):
            text = text[len(prefix):]
            break

    text = text.strip()
    if not text:
        return []

    # Split by separators
    parts = _SEPARATOR_PATTERN.split(text)

    # Clean up each part
    ingredients = []
    for part in parts:
        part = part.strip()
        if part:
            ingredients.append(part)

    return ingredients
