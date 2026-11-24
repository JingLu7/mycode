"""atomcode system prompt 生成器 — 基于逆向得到的 22 段 system prompt"""
from __future__ import annotations
import os
import platform as plat
from pathlib import Path

# 逆向得到的 atomcode system prompt 落盘位置
_SYSTEM_PROMPT_FILE = Path(__file__).resolve().parents[2] / "artifacts" / "recon" / "atomcode" / "system-prompt.md"


def build_atomcode_system_prompt(cwd: str, model: str = "qwen3.8-27b") -> str:
    """构建 atomcode system prompt。

    以逆向落盘的 22 段 system prompt 为基底，替换模型名，追加工作目录信息。
    """
    if _SYSTEM_PROMPT_FILE.exists():
        base = _SYSTEM_PROMPT_FILE.read_text(encoding="utf-8")
    else:
        base = _fallback_prompt()

    # 替换模型名（逆向时用的是 qwen3.8-27b，实际可能不同）
    base = base.replace("qwen3.8-27b", model)

    # 追加工作目录信息（atomcode 在 system-reminder 里注入，这里放末尾）
    footer = f"\n\n---\nCurrent working directory: {cwd}\nPlatform: {plat.system().lower()}"
    return base + footer


def _fallback_prompt() -> str:
    """如果逆向文件不存在，用简化版"""
    return """You are AtomCode, an AI coding agent by AtomGit.

## WORKFLOW
For simple changes: just do it — search, edit, verify, done.
For non-trivial features: UNDERSTAND → SEARCH → PLAN → EDIT → VERIFY → SUMMARIZE.
For bug reports: REPRODUCE → DIAGNOSE → FIX → VERIFY.

## TOOL DISCIPLINE
Do NOT shell out for file work. Use read_file/glob/grep/list_directory instead of bash cat/find/grep.
Use bash ONLY for git, builds, package managers, and running commands.

## EXECUTION DISCIPLINE
FIX, DON'T HIDE: find and fix the ROOT CAUSE.
EDIT WITH THE EDIT TOOL: use edit_file, not sed/awk.
"""