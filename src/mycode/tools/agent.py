"""Agent 工具 — 启动子 agent 处理复杂任务

通过 SubagentManager 启动独立 AgentLoop 实例。
subagent 拥有独立上下文，共享 LLM provider。
"""
from __future__ import annotations

from mycode.harness.subagent import SubagentManager


def execute(
    description: str,
    prompt: str,
    subagent_type: str = "general",
    model: str | None = None,
    effort: str | None = None,
    run_in_background: bool = True,
    isolation: str | None = None,
) -> str:
    """启动子 agent 执行任务"""
    manager = SubagentManager.instance()
    # model/effort/isolation 参数暂不使用，保留接口契约
    return manager.spawn(
        prompt=prompt,
        subagent_type=subagent_type,
        description=description,
    )


TOOL_SCHEMA = {
    "name": "Agent",
    "description": (
        "Launch a new agent to handle complex, multi-step tasks. "
        "The agent runs with its own context and returns a final report. "
        "Use subagent_type to select agent specialization (general, explore, coder)."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "description": {"type": "string", "description": "A short (3-5 word) description of the task."},
            "prompt": {"type": "string", "description": "The task for the agent to perform."},
            "subagent_type": {"type": "string", "description": "The type of specialized agent to use."},
            "model": {"type": "string", "description": "Optional model override (not yet supported)."},
            "effort": {"type": "string", "description": "Reasoning effort level (not yet supported)."},
            "run_in_background": {"type": "boolean", "description": "Run in background (default true). Currently always synchronous."},
            "isolation": {"type": "string", "description": "Isolation mode (not yet supported)."},
        },
        "required": ["description", "prompt"],
    },
    "execute": execute,
}