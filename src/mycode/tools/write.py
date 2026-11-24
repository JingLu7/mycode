"""Write 工具 — 写入文件"""
from __future__ import annotations
from pathlib import Path


def execute(file_path: str, content: str) -> str:
    """写入文件，自动创建父目录"""
    p = Path(file_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"Wrote {len(content)} bytes to {file_path}"


TOOL_SCHEMA = {
    "name": "Write",
    "description": "Write content to a file, creating parent directories if needed.",
    "input_schema": {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Absolute or relative file path."},
            "content": {"type": "string", "description": "The content to write."},
        },
        "required": ["file_path", "content"],
    },
    "execute": execute,
}