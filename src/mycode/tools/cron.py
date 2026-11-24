"""Cron 工具 — 定时任务管理

CronCreate/CronDelete/CronList。
简化版：内存存储 + 可选持久化到 ~/.mycode/scheduled_tasks.json。
cron 表达式解析使用 5 字段（minute hour day month weekday）。
"""
from __future__ import annotations
import json
import os
import time
import uuid
from pathlib import Path


_TASKS_FILE = Path(os.path.expanduser("~/.mycode/scheduled_tasks.json"))

# 进程内任务存储
_tasks: dict[str, dict] = {}


def _load_durable() -> None:
    """加载持久化任务"""
    if _TASKS_FILE.exists():
        try:
            data = json.loads(_TASKS_FILE.read_text())
            for tid, task in data.items():
                _tasks[tid] = task
        except (json.JSONDecodeError, OSError):
            pass


def _save_durable() -> None:
    """保存持久化任务"""
    durable = {k: v for k, v in _tasks.items() if v.get("durable")}
    try:
        _TASKS_FILE.parent.mkdir(parents=True, exist_ok=True)
        _TASKS_FILE.write_text(json.dumps(durable, indent=2, ensure_ascii=False))
    except OSError:
        pass  # 只读文件系统等


def _validate_cron(cron: str) -> bool:
    """简易 cron 表达式验证（5 字段）"""
    parts = cron.split()
    if len(parts) != 5:
        return False
    return True


def cron_create(cron: str, prompt: str, recurring: bool = False, durable: bool = False) -> str:
    """创建定时任务"""
    if not _validate_cron(cron):
        return f"Error: invalid cron expression (expected 5 fields): {cron}"
    _load_durable()
    task_id = f"cron-{uuid.uuid4().hex[:8]}"
    _tasks[task_id] = {
        "id": task_id,
        "cron": cron,
        "prompt": prompt,
        "recurring": recurring,
        "durable": durable,
        "created_at": time.time(),
    }
    if durable:
        _save_durable()
    return f"Created cron job: {task_id} (cron: {cron}, recurring: {recurring}, durable: {durable})"


def cron_delete(id: str) -> str:
    """删除定时任务"""
    _load_durable()
    if id not in _tasks:
        return f"Error: cron job not found: {id}"
    del _tasks[id]
    _save_durable()
    return f"Deleted cron job: {id}"


def cron_list() -> str:
    """列出所有定时任务"""
    _load_durable()
    if not _tasks:
        return "No cron jobs scheduled."
    lines = ["[Cron Jobs]"]
    for task in _tasks.values():
        lines.append(
            f"  {task['id']}: cron={task['cron']} recurring={task['recurring']} durable={task['durable']}"
        )
        lines.append(f"    prompt: {task['prompt'][:80]}")
    return "\n".join(lines)


# Tool schemas
CRON_CREATE_SCHEMA = {
    "name": "CronCreate",
    "description": "Schedule a prompt to be enqueued at a future time using a cron expression.",
    "input_schema": {
        "type": "object",
        "properties": {
            "cron": {"type": "string", "description": "Cron expression (5 fields: minute hour day month weekday)."},
            "prompt": {"type": "string", "description": "The prompt to execute when triggered."},
            "recurring": {"type": "boolean", "description": "Whether this is a recurring task."},
            "durable": {"type": "boolean", "description": "Whether to persist across restarts."},
        },
        "required": ["cron", "prompt"],
    },
    "execute": cron_create,
}

CRON_DELETE_SCHEMA = {
    "name": "CronDelete",
    "description": "Cancel a cron job by its ID.",
    "input_schema": {
        "type": "object",
        "properties": {
            "id": {"type": "string", "description": "The ID of the cron job to delete."},
        },
        "required": ["id"],
    },
    "execute": cron_delete,
}

CRON_LIST_SCHEMA = {
    "name": "CronList",
    "description": "List all scheduled cron jobs.",
    "input_schema": {
        "type": "object",
        "properties": {},
    },
    "execute": cron_list,
}