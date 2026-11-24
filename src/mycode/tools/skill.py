"""Skill 工具 — 调用预定义 skill"""
from __future__ import annotations

from mycode.harness.skills import SkillManager


def execute(skill: str, args: str = "") -> str:
    """调用 skill"""
    manager = SkillManager.instance()
    return manager.invoke(name=skill, args=args)


TOOL_SCHEMA = {
    "name": "Skill",
    "description": (
        "Invoke a skill by name. A skill is a packaged set of instructions for a specific task. "
        "Available skills are loaded from ~/.mycode/skills/*.md."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "skill": {"type": "string", "description": "The name of the skill to invoke."},
            "args": {"type": "string", "description": "Optional arguments for the skill."},
        },
        "required": ["skill"],
    },
    "execute": execute,
}