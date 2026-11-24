"""Messaging 工具 — 消息传递和发现报告

SendMessage / ReportFindings / ScheduleWakeup。
简化版：SendMessage 通过 SubagentManager 向 subagent 发消息，
ReportFindings 格式化输出发现，ScheduleWakeup 记录恢复时间。
"""
from __future__ import annotations
import json
import time
from typing import Any


def send_message(to: str, message: str, summary: str = "", notify_when_idle: bool = False) -> str:
    """向另一个 agent 发送消息"""
    from mycode.harness.subagent import SubagentManager

    manager = SubagentManager.instance()
    running = manager.list_running()
    target = None
    for r in running:
        if r["id"] == to or r.get("description") == to:
            target = r
            break

    if target is None:
        return f"Error: agent '{to}' not found. Use ListAgents to see available agents."

    # 简化：用 SubagentManager 重新 spawn 一个 agent 处理消息
    result = manager.spawn(
        prompt=f"[Message from parent: {message}]\n\n[Summary: {summary}]",
        subagent_type=target.get("subagent_type", "general"),
        description=f"msg-to-{to}",
    )
    return f"Message sent to {to}.\n{result}"


def report_findings(findings: list[dict[str, Any]], level: str = "info") -> str:
    """报告发现（格式化输出）"""
    if not findings:
        return "No findings to report."
    lines = [f"[ReportFindings] level={level}, {len(findings)} finding(s)"]
    for i, f in enumerate(findings, 1):
        lines.append(f"\n{i}. {f.get('title', 'Untitled')}")
        if f.get("file"):
            lines.append(f"   file: {f['file']}")
        if f.get("line"):
            lines.append(f"   line: {f['line']}")
        if f.get("severity"):
            lines.append(f"   severity: {f['severity']}")
        if f.get("message"):
            lines.append(f"   {f['message']}")
    return "\n".join(lines)


def schedule_wakeup(
    delay_seconds: int = 0,
    reason: str = "",
    prompt: str = "",
    stop: bool = False,
    noop: bool = False,
) -> str:
    """安排恢复时间"""
    if noop:
        return "[ScheduleWakeup] noop — no wakeup scheduled"
    if stop:
        return "[ScheduleWakeup] stop — loop will not resume"
    if delay_seconds <= 0:
        return "Error: delay_seconds must be positive"
    wakeup_time = time.time() + delay_seconds
    return (
        f"[ScheduleWakeup] scheduled in {delay_seconds}s (at {time.ctime(wakeup_time)})\n"
        f"reason: {reason}\n"
        f"prompt: {prompt[:100]}"
    )


SEND_MESSAGE_SCHEMA = {
    "name": "SendMessage",
    "description": "Send a message to another agent by name or ID.",
    "input_schema": {
        "type": "object",
        "properties": {
            "to": {"type": "string", "description": "Agent name or ID to send to."},
            "message": {"type": "string", "description": "The message content."},
            "summary": {"type": "string", "description": "Short summary of the message."},
            "notify_when_idle": {"type": "boolean", "description": "Notify when the agent is idle."},
        },
        "required": ["to", "message"],
    },
    "execute": send_message,
}

REPORT_FINDINGS_SCHEMA = {
    "name": "ReportFindings",
    "description": "Report findings as a typed list.",
    "input_schema": {
        "type": "object",
        "properties": {
            "findings": {
                "type": "array",
                "items": {"type": "object"},
                "description": "List of finding objects.",
            },
            "level": {"type": "string", "description": "Report level (info, warning, error)."},
        },
        "required": ["findings"],
    },
    "execute": report_findings,
}

SCHEDULE_WAKEUP_SCHEMA = {
    "name": "ScheduleWakeup",
    "description": "Schedule when to resume work in loop mode.",
    "input_schema": {
        "type": "object",
        "properties": {
            "delaySeconds": {"type": "integer", "description": "Delay in seconds before wakeup."},
            "reason": {"type": "string", "description": "Reason for the wakeup."},
            "prompt": {"type": "string", "description": "Prompt to execute on wakeup."},
            "stop": {"type": "boolean", "description": "Stop the loop."},
            "noop": {"type": "boolean", "description": "No-op (don't schedule)."},
        },
    },
    "execute": schedule_wakeup,
}