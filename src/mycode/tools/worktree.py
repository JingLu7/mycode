"""Worktree 工具 — Git worktree 隔离

EnterWorktree/ExitWorktree。
简化版：用 git worktree add/remove 实现隔离工作目录。
"""
from __future__ import annotations
import subprocess
from pathlib import Path


def enter_worktree(name: str = "", path: str = "") -> str:
    """进入 git worktree"""
    if not name:
        import uuid

        name = f"wt-{uuid.uuid4().hex[:8]}"
    try:
        result = subprocess.run(
            ["git", "worktree", "add", f"../{name}", "-b", name],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return f"Error: git worktree add failed: {result.stderr}"
        return f"Created worktree: {name} at ../{name}\n{result.stdout}"
    except FileNotFoundError:
        return "Error: git not found"
    except subprocess.TimeoutExpired:
        return "Error: git worktree add timed out"


def exit_worktree(action: str, discard_changes: bool = False) -> str:
    """退出 git worktree"""
    if action not in ("merge", "discard"):
        return f"Error: action must be 'merge' or 'discard', got: {action}"
    try:
        # 找到当前 worktree 名
        result = subprocess.run(
            ["git", "worktree", "list"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return f"Error: git worktree list failed: {result.stderr}"

        if discard_changes or action == "discard":
            # 删除 worktree
            result = subprocess.run(
                ["git", "worktree", "remove", "--force", "."],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return f"Exited worktree (discarded changes)\n{result.stdout}"
        else:
            return "Exited worktree (merge not yet implemented — use git merge manually)"
    except FileNotFoundError:
        return "Error: git not found"
    except subprocess.TimeoutExpired:
        return "Error: git worktree operation timed out"


ENTER_WORKTREE_SCHEMA = {
    "name": "EnterWorktree",
    "description": "Create a git worktree for isolated work.",
    "input_schema": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Name for the worktree branch."},
            "path": {"type": "string", "description": "Path for the worktree (optional)."},
        },
    },
    "execute": enter_worktree,
}

EXIT_WORKTREE_SCHEMA = {
    "name": "ExitWorktree",
    "description": "Exit a git worktree and return to the original directory.",
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {"type": "string", "description": "Action: 'merge' or 'discard'."},
            "discard_changes": {"type": "boolean", "description": "Whether to discard changes."},
        },
        "required": ["action"],
    },
    "execute": exit_worktree,
}