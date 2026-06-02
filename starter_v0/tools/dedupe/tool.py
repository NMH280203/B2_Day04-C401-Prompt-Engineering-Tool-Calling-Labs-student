from __future__ import annotations

from typing import Any


def dedupe_items(
    items: list[dict[str, Any]] | None = None,
    by: str = "url",
) -> dict[str, Any]:
    """Remove duplicate research items by url or normalized title."""
    items = items or []
    key_field = "url" if by == "url" else "title"
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for item in items:
        raw = (item.get(key_field) or "").strip().lower()
        if not raw:
            unique.append(item)
            continue
        if raw in seen:
            continue
        seen.add(raw)
        unique.append(item)
    return {
        "tool": "dedupe",
        "by": key_field,
        "input_count": len(items),
        "output_count": len(unique),
        "items": unique,
    }
