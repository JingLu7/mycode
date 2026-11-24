"""Edit 工具 — 精确字符串替换"""
from __future__ import annotations
from pathlib import Path


def execute(file_path: str, old_string: str, new_string: str, replace_all: bool = False) -> str:
    """在文件中精确替换字符串"""
    p = Path(file_path)
    if not p.exists():
        return f"Error: file not found: {file_path}"
    if not p.is_file():
        return f"Error: not a file: {file_path}"

    content = p.read_text(encoding="utf-8", errors="replace")
    count = content.count(old_string)

    if count == 0:
        return f"Error: old_string not found in {file_path}"
    if count > 1 and not replace_all:
        return f"Error: found {count} matches for old_string; provide replace_all=true to replace all, or make old_string unique"

    if replace_all:
        new_content = content.replace(old_string, new_string)
    else:
        new_content = content.replace(old_string, new_string, 1)

    p.write_text(new_content, encoding="utf-8")
    replaced = count if replace_all else 1
    return f"Replaced {replaced} occurrence(s) in {file_path}"


TOOL_SCHEMA = {
    "name": "Edit",
    "description": "Perform an exact string replacement in a file. Fails if old_string is not found or found multiple times (unless replace_all).",
    "input_schema": {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Absolute or relative file path."},
            "old_string": {"type": "string", "description": "The text to replace."},
            "new_string": {"type": "string", "description": "The replacement text."},
            "replace_all": {"type": "boolean", "description": "Replace all occurrences.", "default": False},
        },
        "required": ["file_path", "old_string", "new_string"],
    },
    "execute": execute,
}