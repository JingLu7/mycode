"""atomcode 基礎工具 — bash/read_file/write_file/edit_file/glob/grep/list_directory/search_replace"""
from __future__ import annotations
import os
import re
import glob as globmod
import subprocess
from pathlib import Path


def _sandbox_path(file_path: str, cwd: str) -> str | None:
    """沙箱检查：文件路径必须在 cwd 内"""
    p = Path(file_path).resolve()
    c = Path(cwd).resolve()
    if not str(p).startswith(str(c)):
        return None
    return str(p)


def bash(args: dict, cwd: str = ".") -> str:
    cmd = args.get("command", "")
    timeout = args.get("timeout", 120)
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout, cwd=cwd)
        return r.stdout + (f"\n[stderr] {r.stderr}" if r.stderr else "")
    except subprocess.TimeoutExpired:
        return f"Command timed out after {timeout}s"
    except Exception as e:
        return f"Error: {e}"


def read_file(args: dict, cwd: str = ".") -> str:
    file_path = args.get("file_path", "")
    p = _sandbox_path(file_path, cwd)
    if p is None:
        return f"read_file: {file_path} is outside the world's root {cwd}"
    if not os.path.exists(p):
        return f"File not found: {p}"
    offset = args.get("offset", 0)
    limit = args.get("limit", 2000)
    with open(p, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    return "".join(lines[offset:offset + limit])


def write_file(args: dict, cwd: str = ".") -> str:
    file_path = args.get("file_path", "")
    content = args.get("content", "")
    p = _sandbox_path(file_path, cwd)
    if p is None:
        return f"write_file: {file_path} is outside the world's root {cwd}"
    os.makedirs(os.path.dirname(p), exist_ok=True) if os.path.dirname(p) else None
    with open(p, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Wrote {len(content)} chars to {file_path}"


def edit_file(args: dict, cwd: str = ".") -> str:
    file_path = args.get("file_path", "")
    old_string = args.get("old_string", "")
    new_string = args.get("new_string", "")
    replace_all = args.get("replace_all", False)
    p = _sandbox_path(file_path, cwd)
    if p is None:
        return f"edit_file: {file_path} is outside the world's root {cwd}"
    if not os.path.exists(p):
        return f"File not found: {p}"
    with open(p, "r", encoding="utf-8") as f:
        content = f.read()
    count = content.count(old_string)
    if count == 0:
        return f"old_string not found in {file_path}"
    if count > 1 and not replace_all:
        return f"old_string found {count} times, set replace_all=true to replace all"
    new_content = content.replace(old_string, new_string) if replace_all else content.replace(old_string, new_string, 1)
    with open(p, "w", encoding="utf-8") as f:
        f.write(new_content)
    return f"Replaced {count if replace_all else 1} occurrence(s) in {file_path}"


def glob_tool(args: dict, cwd: str = ".") -> str:
    pattern = args.get("pattern", "**/*")
    path = args.get("path", cwd)
    p = _sandbox_path(path, cwd) or cwd
    matches = globmod.glob(os.path.join(p, pattern), recursive=True)
    return "\n".join(matches[:100]) if matches else "No matches"


def grep_tool(args: dict, cwd: str = ".") -> str:
    pattern = args.get("pattern", "")
    path = args.get("path", cwd)
    max_results = args.get("max_results", 50)
    p = _sandbox_path(path, cwd) or cwd
    results = []
    for root, dirs, files in os.walk(p):
        for fname in files:
            fpath = os.path.join(root, fname)
            try:
                with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                    for i, line in enumerate(f, 1):
                        if re.search(pattern, line):
                            results.append(f"{fpath}:{i}: {line.rstrip()}")
                            if len(results) >= max_results:
                                return "\n".join(results)
            except (IOError, OSError):
                pass
    return "\n".join(results) if results else "No matches"


def list_directory(args: dict, cwd: str = ".") -> str:
    path = args.get("path", cwd)
    depth = args.get("depth", 2)
    p = _sandbox_path(path, cwd) or cwd
    lines = []
    for root, dirs, files in os.walk(p):
        rel = os.path.relpath(root, p)
        level = 0 if rel == "." else rel.count(os.sep) + 1
        if level > depth:
            dirs[:] = []
            continue
        indent = "  " * level
        for d in sorted(dirs):
            lines.append(f"{indent}{d}/")
        for f in sorted(files):
            lines.append(f"{indent}{f}")
    return "\n".join(lines[:200]) if lines else "Empty directory"


def search_replace(args: dict, cwd: str = ".") -> str:
    search = args.get("search", "")
    replace = args.get("replace", "")
    pattern = args.get("glob", "**/*")
    path = args.get("path", cwd)
    use_regex = args.get("regex", False)
    p = _sandbox_path(path, cwd) or cwd
    count = 0
    for fpath in globmod.glob(os.path.join(p, pattern), recursive=True):
        if not os.path.isfile(fpath):
            continue
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
            if use_regex:
                new_content = re.sub(search, replace, content)
            else:
                new_content = content.replace(search, replace)
            if new_content != content:
                with open(fpath, "w", encoding="utf-8") as f:
                    f.write(new_content)
                count += 1
        except (IOError, OSError):
            pass
    return f"Replaced in {count} file(s)"


BASIC_TOOLS = {
    "bash": {
        "description": "Run a shell command in the working directory and return its output.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The shell command to run"},
                "timeout": {"type": "integer", "description": "Timeout in seconds"},
                "intent": {"type": "string", "description": "Why this command is being run"},
            },
            "required": ["command"],
        },
        "execute": bash,
    },
    "read_file": {
        "description": "Read a file — or any slice of one — from the filesystem.",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path to the file"},
                "offset": {"type": "integer", "description": "Line offset to start from"},
                "limit": {"type": "integer", "description": "Max lines to read"},
                "intent": {"type": "string"},
            },
            "required": ["file_path"],
        },
        "execute": read_file,
    },
    "write_file": {
        "description": "Write content to a file: creates it (and any missing parent dirs).",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string"},
                "content": {"type": "string"},
                "intent": {"type": "string"},
            },
            "required": ["file_path", "content"],
        },
        "execute": write_file,
    },
    "edit_file": {
        "description": "Replace an exact text fragment in a file.",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string"},
                "old_string": {"type": "string"},
                "new_string": {"type": "string"},
                "replace_all": {"type": "boolean"},
                "intent": {"type": "string"},
            },
            "required": ["file_path", "old_string", "new_string"],
        },
        "execute": edit_file,
    },
    "glob": {
        "description": "Find files by glob pattern (e.g. `**/*.rs`, `src/**/*.ts`).",
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string"},
                "path": {"type": "string"},
                "intent": {"type": "string"},
            },
            "required": ["pattern"],
        },
        "execute": glob_tool,
    },
    "grep": {
        "description": "Search file contents by regular expression under a directory.",
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string"},
                "path": {"type": "string"},
                "max_results": {"type": "integer"},
                "intent": {"type": "string"},
            },
            "required": ["pattern"],
        },
        "execute": grep_tool,
    },
    "list_directory": {
        "description": "List a directory tree (indented; directories end with '/').",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "depth": {"type": "integer"},
                "intent": {"type": "string"},
            },
            "required": [],
        },
        "execute": list_directory,
    },
    "search_replace": {
        "description": "Find and replace text across MANY files at once.",
        "parameters": {
            "type": "object",
            "properties": {
                "search": {"type": "string"},
                "replace": {"type": "string"},
                "glob": {"type": "string"},
                "path": {"type": "string"},
                "regex": {"type": "boolean"},
                "intent": {"type": "string"},
            },
            "required": ["search", "replace"],
        },
        "execute": search_replace,
    },
}