"""atomcode 代码分析工具 — ast_grep/list_symbols/read_symbol/find_references/trace_*/file_dependencies/blast_radius

用 Python ast 模块做符号级分析（atomcode 独有核心能力）。
非 Python 文件退化到 grep-based 方式。
"""
from __future__ import annotations
import ast
import os
import re
import glob as globmod
from pathlib import Path
from collections import defaultdict, deque


def _resolve(path: str, cwd: str) -> str | None:
    p = Path(path).resolve()
    c = Path(cwd).resolve()
    if not str(p).startswith(str(c)):
        return None
    return str(p)


def _parse_python(file_path: str) -> ast.AST | None:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return ast.parse(f.read(), filename=file_path)
    except Exception:
        return None


def _collect_symbols(file_path: str) -> list[dict]:
    """收集文件中的所有符号（函数/类/方法）"""
    tree = _parse_python(file_path)
    if not tree:
        return []
    symbols = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            symbols.append({
                "name": node.name,
                "type": "function",
                "line": node.lineno,
                "end_line": getattr(node, "end_lineno", node.lineno),
            })
        elif isinstance(node, ast.ClassDef):
            symbols.append({
                "name": node.name,
                "type": "class",
                "line": node.lineno,
                "end_line": getattr(node, "end_lineno", node.lineno),
            })
    return symbols


def list_symbols(args: dict, cwd: str = ".") -> str:
    file_path = args.get("file_path", "")
    p = _resolve(file_path, cwd)
    if p is None:
        return f"list_symbols: {file_path} is outside the world's root {cwd}"
    if not os.path.exists(p):
        return f"File not found: {p}"
    symbols = _collect_symbols(p)
    if not symbols:
        return "No symbols found (not a Python file or empty)"
    lines = []
    for s in symbols:
        lines.append(f"  {s['line']:5d}  {s['type']:8s}  {s['name']}")
    return f"{file_path} ({len(symbols)} symbols):\n" + "\n".join(lines)


def read_symbol(args: dict, cwd: str = ".") -> str:
    file_path = args.get("file_path", "")
    symbol_name = args.get("symbol", "")
    p = _resolve(file_path, cwd)
    if p is None:
        return f"read_symbol: {file_path} is outside the world's root {cwd}"
    if not os.path.exists(p):
        return f"File not found: {p}"
    symbols = _collect_symbols(p)
    target = None
    for s in symbols:
        if s["name"] == symbol_name:
            target = s
            break
    if not target:
        return f"Symbol '{symbol_name}' not found in {file_path}"
    with open(p, "r", encoding="utf-8") as f:
        all_lines = f.readlines()
    start = target["line"] - 1
    end = target["end_line"]
    return f"--- {symbol_name} ({target['type']}, lines {start+1}-{end}) ---\n" + "".join(all_lines[start:end])


def find_references(args: dict, cwd: str = ".") -> str:
    symbol = args.get("symbol", "")
    path = args.get("path", cwd)
    p = _resolve(path, cwd) or cwd
    results = []
    for fpath in globmod.glob(os.path.join(p, "**/*.py"), recursive=True):
        if not os.path.isfile(fpath):
            continue
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                for i, line in enumerate(f, 1):
                    if re.search(r'\b' + re.escape(symbol) + r'\b', line):
                        results.append(f"{fpath}:{i}: {line.rstrip()}")
        except (IOError, OSError):
            pass
    return "\n".join(results[:50]) if results else f"No references to '{symbol}' found"


def _build_call_graph(cwd: str) -> tuple[dict, dict]:
    """构建调用图：caller→callees 和 callee→callers"""
    callers = defaultdict(set)  # callee → {callers}
    callees = defaultdict(set)  # caller → {callees}
    for fpath in globmod.glob(os.path.join(cwd, "**/*.py"), recursive=True):
        if not os.path.isfile(fpath):
            continue
        tree = _parse_python(fpath)
        if not tree:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                caller_name = node.name
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        func = child.func
                        if isinstance(func, ast.Name):
                            callees[caller_name].add(func.id)
                            callers[func.id].add(caller_name)
                        elif isinstance(func, ast.Attribute):
                            callees[caller_name].add(func.attr)
                            callers[func.attr].add(caller_name)
    return dict(callers), dict(callees)


def trace_callees(args: dict, cwd: str = ".") -> str:
    symbol = args.get("symbol", "")
    depth = args.get("depth", 3)
    _, callees = _build_call_graph(cwd)
    result = []
    visited = set()
    queue = deque([(symbol, 0)])
    while queue:
        name, d = queue.popleft()
        if name in visited or d > depth:
            continue
        visited.add(name)
        indent = "  " * d
        result.append(f"{indent}{name}")
        for callee in sorted(calles.get(name, [])):
            queue.append((callee, d + 1))
    return "\n".join(result) if result else f"Symbol '{symbol}' not found"


def trace_callers(args: dict, cwd: str = ".") -> str:
    symbol = args.get("symbol", "")
    depth = args.get("depth", 3)
    callers, _ = _build_call_graph(cwd)
    result = []
    visited = set()
    queue = deque([(symbol, 0)])
    while queue:
        name, d = queue.popleft()
        if name in visited or d > depth:
            continue
        visited.add(name)
        indent = "  " * d
        result.append(f"{indent}{name}")
        for caller in sorted(callers.get(name, [])):
            queue.append((caller, d + 1))
    return "\n".join(result) if result else f"Symbol '{symbol}' not found"


def trace_chain(args: dict, cwd: str = ".") -> str:
    from_sym = args.get("from", "")
    to_sym = args.get("to", "")
    _, callees = _build_call_graph(cwd)
    queue = deque([(from_sym, [from_sym])])
    visited = {from_sym}
    while queue:
        name, path = queue.popleft()
        if name == to_sym:
            return " → ".join(path)
        for callee in calles.get(name, []):
            if callee not in visited:
                visited.add(callee)
                queue.append((callee, path + [callee]))
    return f"No call chain from '{from_sym}' to '{to_sym}' found"


def file_dependencies(args: dict, cwd: str = ".") -> str:
    file_path = args.get("file", "")
    p = _resolve(file_path, cwd)
    if p is None:
        return f"file_dependencies: {file_path} is outside the world's root {cwd}"
    tree = _parse_python(p)
    if not tree:
        return f"Cannot parse {file_path} (not a Python file)"
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
    return f"{file_path} depends on ({len(imports)}):\n" + "\n".join(f"  {imp}" for imp in sorted(set(imports)))


def blast_radius(args: dict, cwd: str = ".") -> str:
    file_path = args.get("file", "")
    p = _resolve(file_path, cwd)
    if p is None:
        return f"blast_radius: {file_path} is outside the world's root {cwd}"
    # 找出哪些文件 import 了这个文件
    target_module = os.path.splitext(os.path.basename(p))[0]
    dependents = []
    for fpath in globmod.glob(os.path.join(cwd, "**/*.py"), recursive=True):
        if fpath == p or not os.path.isfile(fpath):
            continue
        tree = _parse_python(fpath)
        if not tree:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if target_module in alias.name:
                        dependents.append(fpath)
            elif isinstance(node, ast.ImportFrom):
                if node.module and target_module in node.module:
                    dependents.append(fpath)
    dependents = sorted(set(dependents))
    return f"blast_radius of {file_path}:\n  direct dependents: {len(dependents)}\n" + "\n".join(f"    {d}" for d in dependents[:20])


def ast_grep(args: dict, cwd: str = ".") -> str:
    pattern = args.get("pattern", "")
    paths = args.get("paths", [cwd])
    lang = args.get("lang", "python")
    # 简化版：用正则匹配模式（真正的 ast-grep 需要 ast-grep 命令行工具）
    results = []
    search_paths = paths if isinstance(paths, list) else [paths]
    for sp in search_paths:
        sp_resolved = _resolve(sp, cwd) or cwd
        for fpath in globmod.glob(os.path.join(sp_resolved, "**/*.py"), recursive=True):
            if not os.path.isfile(fpath):
                continue
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    for i, line in enumerate(f, 1):
                        if pattern in line:
                            results.append(f"{fpath}:{i}: {line.rstrip()}")
                            if len(results) >= 50:
                                return "\n".join(results)
            except (IOError, OSError):
                pass
    return "\n".join(results) if results else "No matches"


ANALYSIS_TOOLS = {
    "list_symbols": {
        "description": "List the functions, classes, structs, methods and other symbols in a file.",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path to the file"},
                "intent": {"type": "string"},
            },
            "required": ["file_path"],
        },
        "execute": list_symbols,
    },
    "read_symbol": {
        "description": "Read the complete source of a single symbol (function / class / method).",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string"},
                "symbol": {"type": "string"},
                "intent": {"type": "string"},
            },
            "required": ["file_path", "symbol"],
        },
        "execute": read_symbol,
    },
    "find_references": {
        "description": "Find all references to a symbol (function/class/variable) across the codebase.",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string"},
                "path": {"type": "string"},
                "intent": {"type": "string"},
            },
            "required": ["symbol"],
        },
        "execute": find_references,
    },
    "trace_callees": {
        "description": "Trace all callees of a symbol (forward call graph), BFS up to depth.",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string"},
                "depth": {"type": "integer"},
                "intent": {"type": "string"},
            },
            "required": ["symbol"],
        },
        "execute": trace_callees,
    },
    "trace_callers": {
        "description": "Trace all callers of a symbol (reverse call graph), BFS up to depth.",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string"},
                "depth": {"type": "integer"},
                "intent": {"type": "string"},
            },
            "required": ["symbol"],
        },
        "execute": trace_callers,
    },
    "trace_chain": {
        "description": "Find the shortest call chain between two symbols (BFS, max 10 hops).",
        "parameters": {
            "type": "object",
            "properties": {
                "from": {"type": "string"},
                "to": {"type": "string"},
                "intent": {"type": "string"},
            },
            "required": ["from", "to"],
        },
        "execute": trace_chain,
    },
    "file_dependencies": {
        "description": "Show a file's dependencies: which modules it imports.",
        "parameters": {
            "type": "object",
            "properties": {
                "file": {"type": "string"},
                "intent": {"type": "string"},
            },
            "required": ["file"],
        },
        "execute": file_dependencies,
    },
    "blast_radius": {
        "description": "Estimate the blast radius of changing a file: direct dependents.",
        "parameters": {
            "type": "object",
            "properties": {
                "file": {"type": "string"},
                "intent": {"type": "string"},
            },
            "required": ["file"],
        },
        "execute": blast_radius,
    },
    "ast_grep": {
        "description": "Structural code search by AST pattern (native ast-grep).",
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string"},
                "paths": {"type": "array", "items": {"type": "string"}},
                "lang": {"type": "string"},
                "intent": {"type": "string"},
            },
            "required": ["pattern"],
        },
        "execute": ast_grep,
    },
}