"""Read 工具 — 读取文件（对齐 claude-code FileRead 契约）

参数：file_path, offset, limit, pages(PDF 页范围), allow_large
PDF 读取走系统 pdftotext。
"""
from __future__ import annotations
import re
import subprocess
from pathlib import Path

DEFAULT_LIMIT = 2000
MAX_LARGE_LIMIT = 200000


def _read_pdf(p: Path, pages: str | None) -> str:
    """用 pdftotext 读取 PDF，pages 形如 '1-5' / '3' / '10-20'"""
    args = ["pdftotext", "-layout"]
    if pages:
        m = re.match(r"^\s*(\d+)\s*(?:-\s*(\d+))?\s*$", pages)
        if not m:
            return f"Error: invalid pages format '{pages}', expected e.g. '1-5', '3', '10-20'"
        args += ["-f", m.group(1), "-l", m.group(2) or m.group(1)]
    args += [str(p), "-"]
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=60)
    except FileNotFoundError:
        return "Error: pdftotext not found; install poppler-utils to read PDFs"
    except subprocess.TimeoutExpired:
        return "Error: pdftotext timed out"
    if result.returncode != 0:
        return f"Error: pdftotext failed: {result.stderr.strip()}"
    lines = result.stdout.splitlines()
    numbered = [f"{i}: {ln}" for i, ln in enumerate(lines, 1)]
    header = f"[PDF: {p.name}" + (f", pages {pages}" if pages else "") + "]"
    return header + "\n" + "\n".join(numbered)


def execute(
    file_path: str,
    offset: int = 1,
    limit: int = DEFAULT_LIMIT,
    pages: str | None = None,
    allow_large: bool = False,
) -> str:
    """读取文件内容，支持行偏移、行数限制、PDF 页范围、大文件整体读"""
    p = Path(file_path)
    if not p.exists():
        return f"Error: file not found: {file_path}"
    if p.is_dir():
        entries = sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name))
        lines = [f"{e.name}{'/' if e.is_dir() else ''}" for e in entries]
        return "\n".join(lines) if lines else "(empty directory)"

    if p.suffix.lower() == ".pdf" or pages:
        return _read_pdf(p, pages)

    text = p.read_text(encoding="utf-8", errors="replace")
    all_lines = text.splitlines()
    effective_limit = MAX_LARGE_LIMIT if allow_large else limit
    start = offset if offset > 0 else 1
    selected = all_lines[start - 1 : start - 1 + effective_limit]
    numbered = [f"{i + start}: {line}" for i, line in enumerate(selected)]
    if not numbered:
        return "(empty file)"
    consumed = start - 1 + effective_limit
    if len(all_lines) > consumed:
        numbered.append(f"... ({len(all_lines) - consumed} more lines; use offset to continue)")
    return "\n".join(numbered)


TOOL_SCHEMA = {
    "name": "Read",
    "description": "Read a file with line numbers. If path is a directory, list entries. Supports PDF pages and large-file reads.",
    "input_schema": {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Absolute or relative file path."},
            "offset": {"type": "integer", "description": "Line number to start reading from (1-indexed).", "default": 1},
            "limit": {"type": "integer", "description": "Maximum number of lines to read.", "default": DEFAULT_LIMIT},
            "pages": {"type": "string", "description": "Page range for PDF files (e.g. '1-5', '3', '10-20'). Max 20 pages."},
            "allow_large": {"type": "boolean", "description": "Read a text file over the usual size limits."},
        },
        "required": ["file_path"],
    },
    "execute": execute,
}
