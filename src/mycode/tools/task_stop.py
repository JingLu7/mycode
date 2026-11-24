"""TaskStop 工具 — 停止后台任务

通过进程内任务注册表管理后台任务。其他工具（如 Bash 的后台模式）
可将任务注册到 TaskRegistry，TaskStop 通过 task_id 停止。
"""
from __future__ import annotations
import os
import signal


class TaskRegistry:
    """进程内后台任务注册表"""

    _instance: "TaskRegistry | None" = None

    def __init__(self) -> None:
        self._tasks: dict[str, dict] = {}

    @classmethod
    def instance(cls) -> "TaskRegistry":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register(self, task_id: str, pid: int, description: str = "") -> None:
        self._tasks[task_id] = {"pid": pid, "description": description}

    def unregister(self, task_id: str) -> None:
        self._tasks.pop(task_id, None)

    def list_tasks(self) -> dict[str, dict]:
        return dict(self._tasks)

    def stop(self, task_id: str) -> bool:
        task = self._tasks.get(task_id)
        if task is None:
            return False
        try:
            os.kill(task["pid"], signal.SIGTERM)
        except ProcessLookupError:
            pass
        except OSError:
            try:
                os.kill(task["pid"], signal.SIGKILL)
            except OSError:
                pass
        self.unregister(task_id)
        return True


def execute(task_id: str, shell_id: str | None = None) -> str:
    """停止后台任务"""
    # shell_id 是废弃参数，兼容
    tid = task_id or shell_id
    if not tid:
        return "Error: task_id is required"
    registry = TaskRegistry.instance()
    if registry.stop(tid):
        return f"Stopped task: {tid}"
    return f"Error: task not found: {tid}"


TOOL_SCHEMA = {
    "name": "TaskStop",
    "description": "Stop a running background task by its ID. Returns success or failure status.",
    "input_schema": {
        "type": "object",
        "properties": {
            "task_id": {"type": "string", "description": "The ID of the background task to stop."},
            "shell_id": {"type": "string", "description": "Deprecated: use task_id instead."},
        },
    },
    "execute": execute,
}