"""Glob 工具 — 文件模式匹配搜索"""
from __future__ import annotations
from pathlib import Path


def execute(pattern: str, path: str = ".") -> str:
    """按 glob 模式搜索文件"""
    base = Path(path)
    if not base.exists():
        return f"Error: path not found: {path}"

    matches = sorted(base.glob(pattern), key=lambda p: p.name)
    if not matches:
        return f"No files matching '{pattern}' in {path}"

    lines = []
    for m in matches[:200]:
        rel = m.relative_to(base) if base != Path(".") else m
        prefix = "/" if m.is_dir() else ""
        lines.append(f"{rel}{prefix}")
    result = "\n".join(lines)
    if len(matches) > 200:
        result += f"\n... and {len(matches) - 200} more"
    return result


TOOL_SCHEMA = {
    "name": "Glob",
    "description": "Find files matching a glob pattern (e.g. '**/*.py'). Returns up to 200 matches.",
    "input_schema": {
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "description": "Glob pattern, e.g. '**/*.py' or 'src/**/*.ts'."},
            "path": {"type": "string", "description": "Directory to search in.", "default": "."},
        },
        "required": ["pattern"],
    },
    "execute": execute,
}