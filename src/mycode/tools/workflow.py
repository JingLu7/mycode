"""Workflow 工具 — 编排多 subagent 工作流

简化版：workflow 是 JSON 脚本，定义一系列 agent 任务。
按顺序执行每个步骤，收集结果。
"""
from __future__ import annotations
import json
import uuid
from typing import Any


def execute(
    script: str = "",
    name: str = "",
    description: str = "",
    title: str = "",
    args: str = "",
    scriptPath: str = "",
    resumeFromRunId: str = "",
) -> str:
    """执行 workflow 脚本"""
    if not script and not scriptPath:
        return "Error: either script or scriptPath is required"

    # 解析 workflow 脚本
    try:
        if scriptPath:
            from pathlib import Path

            script = Path(scriptPath).read_text()
        workflow = json.loads(script)
    except json.JSONDecodeError as e:
        return f"Error: invalid workflow JSON: {e}"
    except FileNotFoundError:
        return f"Error: script file not found: {scriptPath}"

    if not isinstance(workflow, dict):
        return "Error: workflow must be a JSON object"

    steps = workflow.get("steps", [])
    if not steps:
        return "Error: workflow has no steps"

    run_id = f"wf-{uuid.uuid4().hex[:8]}"
    from mycode.harness.subagent import SubagentManager

    manager = SubagentManager.instance()
    results = []

    for i, step in enumerate(steps):
        step_name = step.get("name", f"step-{i}")
        step_prompt = step.get("prompt", "")
        step_type = step.get("subagent_type", "general")

        if args:
            step_prompt += f"\n\n[Workflow args: {args}]"

        result = manager.spawn(
            prompt=step_prompt,
            subagent_type=step_type,
            description=f"wf:{step_name}",
        )
        results.append(f"[{step_name}] {result}")

    return f"[Workflow: {name or run_id}]\n{'='*40}\n" + "\n\n".join(results)


TOOL_SCHEMA = {
    "name": "Workflow",
    "description": "Execute a workflow script that orchestrates multiple subagents. The script is a JSON object with a 'steps' array.",
    "input_schema": {
        "type": "object",
        "properties": {
            "script": {"type": "string", "description": "Workflow script as JSON string."},
            "name": {"type": "string", "description": "Workflow name."},
            "description": {"type": "string", "description": "Workflow description."},
            "title": {"type": "string", "description": "Display title."},
            "args": {"type": "string", "description": "Arguments to pass to the workflow."},
            "scriptPath": {"type": "string", "description": "Path to a workflow script file."},
            "resumeFromRunId": {"type": "string", "description": "Resume from a previous run ID."},
        },
    },
    "execute": execute,
}