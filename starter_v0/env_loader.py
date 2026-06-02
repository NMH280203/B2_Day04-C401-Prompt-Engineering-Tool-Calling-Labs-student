from __future__ import annotations

import os
from pathlib import Path


def _strip_inline_comment(value: str) -> str:
    """Strip trailing inline comments (# ...) unless the value is quoted."""
    if value.startswith(("'", '"')):
        return value  # quoted — strip outer quotes only, no comment handling needed
    # Remove inline comment: first ' #' or '\t#' that appears after content
    for i, ch in enumerate(value):
        if ch == "#" and i > 0 and value[i - 1] in (" ", "\t"):
            return value[:i].rstrip()
    return value


def load_dotenv(path: Path, *, override: bool = True) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = _strip_inline_comment(value.strip()).strip("\"'")
        if key and (override or key not in os.environ):
            os.environ[key] = value


def load_lab_env(root: Path) -> None:
    external_path = os.getenv("DAY04_ENV_FILE")
    if external_path:
        load_dotenv(Path(external_path).expanduser())
        return
    load_dotenv(root / ".env")
