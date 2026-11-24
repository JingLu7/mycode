"""ListAgents 工具 — 列出可用 agent 类型和运行中的实例"""
from __future__ import annotations

from mycode.harness.subagent import SubagentManager


def execute(channel: str | None = None, q: str | None = None) -> str:
    """列出可用 agent 类型"""
    manager = SubagentManager.instance()

    lines = ["[Available Agent Types]"]
    for atype in manager.list_types():
        tools = atype.get("tools")
        tools_str = ", ".join(tools) if tools else "(all tools)"
        lines.append(f"  {atype['name']}: {atype['description']}")
        lines.append(f"    tools: {tools_str}")

    running = manager.list_running()
    if running:
        lines.append("\n[Running Subagents]")
        for r in running:
            lines.append(f"  {r['id']} ({r.get('subagent_type', '?')}): {r.get('status', '?')} — {r.get('description', '')}")

    return "\n".join(lines)


TOOL_SCHEMA = {
    "name": "ListAgents",
    "description": "List available agent types and running subagent instances.",
    "input_schema": {
        "type": "object",
        "properties": {
            "channel": {"type": "string", "description": "Not available; leave unset."},
            "q": {"type": "string", "description": "Not available; leave unset."},
        },
    },
    "execute": execute,
}