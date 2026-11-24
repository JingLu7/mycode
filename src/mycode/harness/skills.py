"""Skill 管理器 — 加载和调用 skill

skill 是带 YAML frontmatter 的 markdown，放在 ~/.mycode/skills/ 下。
对齐 claude-code：支持目录结构 <name>/SKILL.md + agents/ assets/ references/ scripts/，
同时兼容单文件 <name>.md。调用 skill 时返回内容作为指令，或在 subagent 中运行。
"""
from __future__ import annotations
import os
import re
from pathlib import Path
from typing import Any


class SkillDef:
    """skill 定义

    claude-code 的 skill 是目录结构：<name>/SKILL.md + agents/ assets/ references/ scripts/。
    mycode 兼容两种：目录 <name>/SKILL.md 与单文件 <name>.md。
    """

    def __init__(self, name: str, description: str, content: str,
                 subagent: bool = False, path: str = "", resources: dict | None = None) -> None:
        self.name = name
        self.description = description
        self.content = content
        self.subagent = subagent
        self.path = path
        self.resources = resources or {}  # {"agents": [...], "assets": [...], ...}

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "subagent": self.subagent,
            "path": self.path,
            "resources": self.resources,
        }


def _parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """解析 YAML frontmatter（简易，不依赖 yaml 库）"""
    meta: dict[str, Any] = {}
    match = re.match(r"^---\n(.*?)\n---\n(.*)", text, re.DOTALL)
    if not match:
        return meta, text
    frontmatter_text = match.group(1)
    body = match.group(2)
    # 简易 YAML 解析（key: value）
    for line in frontmatter_text.strip().splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip()
            if value.lower() in ("true", "false"):
                meta[key] = value.lower() == "true"
            else:
                meta[key] = value
    return meta, body


class SkillManager:
    """skill 管理器（进程内单例）"""

    _instance: "SkillManager | None" = None

    def __init__(self) -> None:
        self._skills: dict[str, SkillDef] = {}
        self._load_builtin()
        self._load_from_dir()

    @classmethod
    def instance(cls) -> "SkillManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load_builtin(self) -> None:
        """加载内置 skill"""
        self._skills["help"] = SkillDef(
            name="help",
            description="Show available skills and their descriptions",
            content="# Help\n\nUse the Skill tool to invoke a skill by name. Use ListAgents to see available agent types.",
        )

    def _load_from_dir(self) -> None:
        """从 ~/.mycode/skills/ 加载 skill（目录 <name>/SKILL.md 优先，兼容单文件 <name>.md）"""
        skills_dir = Path(os.path.expanduser("~/.mycode/skills"))
        if not skills_dir.is_dir():
            return
        # 1. 目录结构：<name>/SKILL.md + agents/ assets/ references/ scripts/
        for d in skills_dir.iterdir():
            if not d.is_dir():
                continue
            skill_md = d / "SKILL.md"
            if not skill_md.is_file():
                continue
            text = skill_md.read_text(encoding="utf-8", errors="replace")
            meta, body = _parse_frontmatter(text)
            name = meta.get("name", d.name)
            self._skills[name] = SkillDef(
                name=name,
                description=meta.get("description", ""),
                content=body.strip(),
                subagent=meta.get("subagent", False),
                path=str(skill_md),
                resources=self._scan_resources(d),
            )
        # 2. 单文件：<name>.md
        for p in skills_dir.glob("*.md"):
            text = p.read_text(encoding="utf-8", errors="replace")
            meta, body = _parse_frontmatter(text)
            name = meta.get("name", p.stem)
            self._skills[name] = SkillDef(
                name=name,
                description=meta.get("description", ""),
                content=body.strip(),
                subagent=meta.get("subagent", False),
                path=str(p),
            )

    @staticmethod
    def _scan_resources(d: Path) -> dict:
        """扫描 skill 目录的标准子目录（对齐 claude-code）。"""
        resources: dict = {}
        for sub in ("agents", "assets", "references", "scripts"):
            sd = d / sub
            if sd.is_dir():
                resources[sub] = [f.name for f in sorted(sd.iterdir()) if f.is_file()]
        return resources

    def reload(self) -> None:
        """重新加载 skill 文件"""
        self._skills.clear()
        self._load_builtin()
        self._load_from_dir()

    def list_skills(self) -> list[dict[str, Any]]:
        """列出所有可用 skill"""
        return [s.to_dict() for s in self._skills.values()]

    def get(self, name: str) -> SkillDef | None:
        return self._skills.get(name)

    def invoke(self, name: str, args: str = "") -> str:
        """调用 skill，返回内容或启动 subagent"""
        skill = self._skills.get(name)
        if skill is None:
            available = ", ".join(self._skills.keys())
            return f"Error: unknown skill '{name}'. Available: {available}"

        if skill.subagent:
            # 在 subagent 中运行
            from mycode.harness.subagent import SubagentManager

            manager = SubagentManager.instance()
            prompt = skill.content
            if args:
                prompt += f"\n\n[Arguments: {args}]"
            return manager.spawn(
                prompt=prompt,
                subagent_type="general",
                description=f"skill:{name}",
            )
        else:
            # 返回 skill 内容作为指令
            result = f"[Skill: {name}]\n{skill.content}"
            if args:
                result += f"\n\n[Arguments: {args}]"
            return result