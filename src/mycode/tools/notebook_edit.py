"""NotebookEdit 工具 — 编辑 Jupyter notebook 单元格

支持 replace/insert/delete 三种模式，操作 .ipynb 文件。
"""
from __future__ import annotations
import json
import uuid
from pathlib import Path


def _read_notebook(path: str) -> dict | None:
    """读取 .ipynb 文件，失败返回 None"""
    p = Path(path)
    if not p.exists():
        return None
    with open(p, "r", encoding="utf-8") as f:
        nb = json.load(f)
    # 确保有 cells
    if "cells" not in nb:
        nb["cells"] = []
    return nb


def _write_notebook(path: str, nb: dict) -> None:
    """写入 .ipynb 文件"""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)
        f.write("\n")


def _find_cell_index(nb: dict, cell_id: str) -> int:
    """按 cell id 查找单元格索引，未找到返回 -1"""
    for i, cell in enumerate(nb["cells"]):
        if cell.get("id") == cell_id:
            return i
    return -1


def _make_cell(cell_type: str, source: str) -> dict:
    """创建新单元格"""
    return {
        "cell_type": cell_type,
        "id": str(uuid.uuid4())[:8],
        "metadata": {},
        "source": source.splitlines(keepends=True),
        "outputs": [] if cell_type == "code" else None,
        "execution_count": None if cell_type == "code" else None,
    }


def execute(
    notebook_path: str,
    new_source: str,
    cell_id: str | None = None,
    cell_type: str | None = None,
    edit_mode: str = "replace",
) -> str:
    """编辑 notebook 单元格"""
    nb = _read_notebook(notebook_path)
    if nb is None:
        return f"Error: notebook not found: {notebook_path}"

    if edit_mode == "replace":
        if not cell_id:
            return "Error: cell_id is required for replace mode"
        idx = _find_cell_index(nb, cell_id)
        if idx < 0:
            return f"Error: cell not found: {cell_id}"
        cell = nb["cells"][idx]
        if cell_type:
            cell["cell_type"] = cell_type
        cell["source"] = new_source.splitlines(keepends=True)
        if cell["cell_type"] == "code" and "outputs" not in cell:
            cell["outputs"] = []
        result = f"Replaced cell {cell_id} (index {idx})"

    elif edit_mode == "insert":
        if not cell_type:
            return "Error: cell_type is required for insert mode"
        new_cell = _make_cell(cell_type, new_source)
        if cell_id:
            idx = _find_cell_index(nb, cell_id)
            if idx < 0:
                return f"Error: cell not found: {cell_id}"
            nb["cells"].insert(idx + 1, new_cell)
            result = f"Inserted new {cell_type} cell after {cell_id} (index {idx + 1})"
        else:
            nb["cells"].insert(0, new_cell)
            result = f"Inserted new {cell_type} cell at beginning (index 0)"

    elif edit_mode == "delete":
        if not cell_id:
            return "Error: cell_id is required for delete mode"
        idx = _find_cell_index(nb, cell_id)
        if idx < 0:
            return f"Error: cell not found: {cell_id}"
        nb["cells"].pop(idx)
        result = f"Deleted cell {cell_id} (was at index {idx})"

    else:
        return f"Error: unknown edit_mode: {edit_mode}"

    _write_notebook(notebook_path, nb)
    return result


TOOL_SCHEMA = {
    "name": "NotebookEdit",
    "description": (
        "Replace, insert, or delete a single cell in a Jupyter notebook (.ipynb). "
        "edit_mode: replace (default), insert, delete. "
        "cell_id required for replace/delete. cell_type required for insert."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "notebook_path": {"type": "string", "description": "Absolute path to the .ipynb file."},
            "cell_id": {"type": "string", "description": "The ID of the cell to edit."},
            "new_source": {"type": "string", "description": "The new source for the cell."},
            "cell_type": {"type": "string", "enum": ["code", "markdown"], "description": "Cell type (code or markdown)."},
            "edit_mode": {"type": "string", "enum": ["replace", "insert", "delete"], "description": "Edit mode. Defaults to replace."},
        },
        "required": ["notebook_path", "new_source"],
    },
    "execute": execute,
}