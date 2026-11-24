"""TodoWrite 工具 — 任务清单（对齐 claude-code TodoWrite 契约）

参数：todos（数组，每项含 content/status/activeForm）。
维护进程内任务清单并返回格式化输出。
"""
from __future__ import annotations

_todos: list[dict] = []

_STATUS_MARK = {"completed": "[x]", "in_progress": "[~]", "pending": "[ ]"}


def execute(todos: list[dict] | None = None, **kwargs) -> str:
    """写入/更新任务清单"""
    global _todos
    if todos is None:
        todos = []
    if not isinstance(todos, list):
        return "Error: todos must be an array"

    validated: list[dict] = []
    for i, t in enumerate(todos):
        if not isinstance(t, dict):
            return f"Error: todos[{i}] must be an object"
        status = t.get("status", "pending")
        if status not in _STATUS_MARK:
            return f"Error: todos[{i}].status must be one of pending|in_progress|completed"
        validated.append({
            "content": t.get("content", ""),
            "status": status,
            "activeForm": t.get("activeForm", ""),
        })
    _todos = validated

    if not validated:
        return "(todo list cleared)"

    lines = ["[TodoWrite] " + _summary(validated)]
    for t in validated:
        mark = _STATUS_MARK[t["status"]]
        lines.append(f"  {mark} {t['content']}")
        if t["activeForm"] and t["status"] == "in_progress":
            lines.append(f"       (doing: {t['activeForm']})")
    return "\n".join(lines)


def _summary(todos: list[dict]) -> str:
    done = sum(1 for t in todos if t["status"] == "completed")
    active = sum(1 for t in todos if t["status"] == "in_progress")
    return f"{done}/{len(todos)} completed, {active} in progress"


TOOL_SCHEMA = {
    "name": "TodoWrite",
    "description": "Create and manage a structured task list. Each todo has content, status (pending|in_progress|completed), and activeForm.",
    "input_schema": {
        "type": "object",
        "properties": {
            "todos": {
                "type": "array",
                "description": "The full todo list.",
                "items": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string", "description": "Brief description of the task."},
                        "status": {"type": "string", "enum": ["pending", "in_progress", "completed"], "description": "Task status."},
                        "activeForm": {"type": "string", "description": "Present-continuous form of the task."},
                    },
                    "required": ["content", "status", "activeForm"],
                },
            },
        },
        "required": ["todos"],
    },
    "execute": execute,
}