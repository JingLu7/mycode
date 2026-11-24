"""Grep 工具 — 内容搜索（对齐 claude-code Grep 契约）

完整参数：pattern, path, glob, output_mode, -A/-B/-C/context, -n, -i, -o,
type, head_limit, offset, multiline。
"""
from __future__ import annotations
import fnmatch
import re
from pathlib import Path

_TYPE_EXT = {
    "py": [".py"], "js": [".js", ".mjs", ".cjs"], "ts": [".ts"], "tsx": [".tsx"],
    "jsx": [".jsx"], "rs": [".rs"], "go": [".go"], "java": [".java"],
    "c": [".c", ".h"], "cpp": [".cpp", ".hpp", ".cc", ".h"], "md": [".md"],
    "json": [".json"], "yaml": [".yaml", ".yml"], "html": [".html"],
    "css": [".css"], "sh": [".sh"], "rb": [".rb"], "toml": [".toml"],
}


def _rel(f: Path, base: Path) -> str:
    try:
        return str(f.relative_to(base)) if base != Path(".") else str(f)
    except ValueError:
        return str(f)


def _collect_files(base: Path, glob_pat: str | None, ftype: str | None) -> list[Path]:
    if base.is_file():
        return [base]
    exts = _TYPE_EXT.get(ftype.lower(), [f".{ftype.lower()}"]) if ftype else None
    pat = glob_pat.lstrip("*").lstrip("/") if glob_pat and glob_pat.startswith("**/") else glob_pat
    files: list[Path] = []
    for f in sorted(base.rglob("*")):
        if not f.is_file():
            continue
        if pat and not fnmatch.fnmatch(f.name, pat):
            continue
        if exts and f.suffix.lower() not in exts:
            continue
        files.append(f)
    return files


def execute(
    pattern: str,
    path: str = ".",
    glob: str | None = None,
    output_mode: str = "files_with_matches",
    **kwargs,
) -> str:
    """在文件内容中搜索正则表达式"""
    before = kwargs.get("-B") or 0
    after = kwargs.get("-A") or 0
    ctx = kwargs.get("context")
    if ctx:
        before = after = ctx
    show_lineno = kwargs.get("-n", True)
    ignore_case = kwargs.get("-i", False)
    only_match = kwargs.get("-o", False)
    ftype = kwargs.get("type")
    head_limit = kwargs.get("head_limit", 250)
    offset = kwargs.get("offset") or 0
    multiline = kwargs.get("multiline", False)

    base = Path(path)
    if not base.exists():
        return f"Error: path not found: {path}"

    flags = re.MULTILINE
    if ignore_case:
        flags |= re.IGNORECASE
    if multiline:
        flags |= re.DOTALL
    try:
        regex = re.compile(pattern, flags)
    except re.error as e:
        return f"Error: invalid regex: {e}"

    files = _collect_files(base, glob, ftype)
    files_hit: list[str] = []
    counts: list[str] = []
    content: list[str] = []

    for f in files:
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        matches = list(regex.finditer(text))
        if not matches:
            continue
        rp = _rel(f, base)
        files_hit.append(rp)
        counts.append(f"{rp}: {len(matches)}")

        if output_mode == "content":
            lines = text.splitlines()
            if multiline:
                for m in matches:
                    content.append(f"{rp}: {m.group(0)[:200]}")
            else:
                hit_lines = sorted({text.count("\n", 0, m.start()) for m in matches})
                for ln in hit_lines:
                    lo, hi = max(0, ln - before), min(len(lines), ln + after + 1)
                    for i in range(lo, hi):
                        marker = ":" if i == ln else "-"
                        raw = lines[i]
                        if only_match and i == ln:
                            parts = [mm.group(0) for mm in regex.finditer(raw)]
                            raw = " ".join(parts) if parts else raw
                        prefix = f"{rp}{marker}{i + 1}{marker}" if show_lineno else f"{rp}{marker}"
                        content.append(f"{prefix} {raw}")

    if output_mode == "files_with_matches":
        out = files_hit
    elif output_mode == "count":
        out = counts
    elif output_mode == "content":
        out = content
    else:
        return f"Error: invalid output_mode '{output_mode}' (content|files_with_matches|count)"

    out = out[offset:]
    if head_limit:
        out = out[:head_limit]
    if not out:
        return f"No matches for '{pattern}' in {path}"
    return "\n".join(out)


TOOL_SCHEMA = {
    "name": "Grep",
    "description": "Search file contents by regular expression (ripgrep-like). Supports output modes, context lines, and filters.",
    "input_schema": {
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "description": "The regular expression pattern to search for."},
            "path": {"type": "string", "description": "File or directory to search in. Defaults to cwd."},
            "glob": {"type": "string", "description": "Glob pattern to filter files (e.g. '*.py')."},
            "output_mode": {"type": "string", "enum": ["content", "files_with_matches", "count"], "description": "Output mode. Defaults to files_with_matches."},
            "-A": {"type": "integer", "description": "Lines to show after each match."},
            "-B": {"type": "integer", "description": "Lines to show before each match."},
            "-C": {"type": "integer", "description": "Alias for context."},
            "context": {"type": "integer", "description": "Lines to show before and after each match."},
            "-n": {"type": "boolean", "description": "Show line numbers. Defaults to true."},
            "-i": {"type": "boolean", "description": "Case insensitive search."},
            "-o": {"type": "boolean", "description": "Print only the matched parts."},
            "type": {"type": "string", "description": "File type to search (py, js, ts, rs, go, java, ...)."},
            "head_limit": {"type": "integer", "description": "Limit output to first N entries. Defaults to 250."},
            "offset": {"type": "integer", "description": "Skip first N entries before applying head_limit."},
            "multiline": {"type": "boolean", "description": "Enable multiline mode where . matches newlines."},
        },
        "required": ["pattern"],
    },
    "execute": execute,
}
