"""权限管理 — 控制工具调用的执行许可"""
from __future__ import annotations
from enum import Enum
from typing import Any


class PermissionMode(str, Enum):
    DEFAULT = "default"              # 危险操作需用户确认
    ACCEPT_EDITS = "acceptEdits"     # 自动接受文件编辑（Write/Edit）
    PLAN = "plan"                    # 只读模式，不执行任何修改
    BYPASS = "bypassPermissions"     # 跳过所有权限检查（对齐 claude-code）


# 工具风险等级（read 自动通过；write/bash 视模式而定）
_RISK_LEVELS: dict[str, str] = {
    "Read": "read",
    "Glob": "read",
    "Grep": "read",
    "WebFetch": "read",
    "WebSearch": "read",
    "TodoWrite": "read",
    "Write": "write",
    "Edit": "write",
    "NotebookEdit": "write",
    "Bash": "bash",
}


class PermissionManager:
    """管理工具调用权限"""

    def __init__(
        self,
        mode: PermissionMode = PermissionMode.DEFAULT,
        allow_rules: list[str] | None = None,
        deny_rules: list[str] | None = None,
    ) -> None:
        self.mode = mode
        self.allow_rules = allow_rules or []
        self.deny_rules = deny_rules or []

    def _matches_any(self, rules: list[str], tool_name: str) -> bool:
        """规则匹配：支持 '*' 通配、精确名、前缀 'Bash*'。"""
        for r in rules:
            if r == "*" or r == tool_name:
                return True
            if r.endswith("*") and tool_name.startswith(r[:-1]):
                return True
        return False

    def check(self, tool_name: str, arguments: dict[str, Any]) -> bool:
        """检查工具调用是否被允许，返回 True 表示允许执行。"""
        # deny 规则优先
        if self._matches_any(self.deny_rules, tool_name):
            return False
        # allow 规则
        if self._matches_any(self.allow_rules, tool_name):
            return True

        if self.mode == PermissionMode.BYPASS:
            return True

        risk = _RISK_LEVELS.get(tool_name, "bash")

        # plan：只读，仅 read 类工具
        if self.mode == PermissionMode.PLAN:
            return risk == "read"

        # acceptEdits：自动接受 read/write，bash 仍需确认
        if self.mode == PermissionMode.ACCEPT_EDITS:
            if risk in ("read", "write"):
                return True
            return self._ask_user(tool_name, arguments)

        # default：read 自动通过，write/bash 需确认
        if risk == "read":
            return True
        return self._ask_user(tool_name, arguments)

    def _ask_user(self, tool_name: str, arguments: dict[str, Any]) -> bool:
        """向用户确认是否执行"""
        # 非交互环境（如 -p 模式）默认拒绝危险操作
        # 交互环境可以读 stdin
        import sys
        if not sys.stdin.isatty():
            # 非交互模式：打印警告但允许执行（P1 简化处理）
            print(f"[warn] auto-approving {tool_name} in non-interactive mode", file=sys.stderr, flush=True)
            return True

        # 交互模式：询问用户
        arg_preview = str(arguments)
        if len(arg_preview) > 200:
            arg_preview = arg_preview[:200] + "..."
        print(f"\n[permission] {tool_name}({arg_preview})", file=sys.stderr, flush=True)
        try:
            answer = input("Allow? [y/N] ").strip().lower()
            return answer in ("y", "yes")
        except (EOFError, KeyboardInterrupt):
            return False