"""Hooks 机制 — 工具调用和生命周期事件的钩子

对齐 claude-code 的 9 种事件：PreToolUse / PostToolUse / Notification / Stop /
SubagentStop / PreCompact / SessionStart / SessionEnd / UserPromptSubmit。
PreToolUse 可阻止或修改工具调用；PostToolUse 可修改结果。
"""
from __future__ import annotations
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class HookType(Enum):
    PRE_TOOL_USE = "pre_tool_use"
    POST_TOOL_USE = "post_tool_use"
    NOTIFICATION = "notification"
    STOP = "stop"
    SUBAGENT_STOP = "subagent_stop"
    PRE_COMPACT = "pre_compact"
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    USER_PROMPT_SUBMIT = "user_prompt_submit"


@dataclass
class Hook:
    """单个钩子定义"""
    hook_type: HookType
    handler: Callable[..., Any] | str  # Python callable 或 shell 命令字符串
    tool_name: str | None = None  # 按工具名过滤（None = 所有工具）
    name: str = ""  # 钩子名称（便于调试）


@dataclass
class PreToolResult:
    """PreToolUse 钩子返回值"""
    allowed: bool = True
    modified_args: dict[str, Any] | None = None
    message: str = ""


class HookManager:
    """钩子管理器"""

    def __init__(self) -> None:
        self._hooks: list[Hook] = []

    def register(self, hook: Hook) -> None:
        self._hooks.append(hook)

    def register_callable(
        self,
        hook_type: HookType,
        handler: Callable[..., Any],
        tool_name: str | None = None,
        name: str = "",
    ) -> None:
        self.register(Hook(hook_type=hook_type, handler=handler, tool_name=tool_name, name=name))

    def register_shell(
        self,
        hook_type: HookType,
        command: str,
        tool_name: str | None = None,
        name: str = "",
    ) -> None:
        self.register(Hook(hook_type=hook_type, handler=command, tool_name=tool_name, name=name))

    def _matches(self, hook: Hook, tool_name: str | None) -> bool:
        """检查钩子是否匹配当前工具"""
        if hook.tool_name is None:
            return True
        return hook.tool_name == tool_name

    def _run_handler(self, hook: Hook, context: dict[str, Any]) -> Any:
        """执行钩子 handler（callable 或 shell 命令）"""
        if callable(hook.handler):
            return hook.handler(context)
        else:
            # shell 命令：传入 context 作为环境变量
            env = {f"HOOK_{k}": str(v) for k, v in context.items()}
            result = subprocess.run(
                hook.handler, shell=True, capture_output=True, text=True, env={**env}
            )
            return result.stdout.strip()

    def fire_pre_tool_use(self, tool_name: str, arguments: dict[str, Any]) -> PreToolResult:
        """触发 PreToolUse 钩子"""
        result = PreToolResult(allowed=True)
        context = {"tool_name": tool_name, "arguments": arguments}

        for hook in self._hooks:
            if hook.hook_type != HookType.PRE_TOOL_USE:
                continue
            if not self._matches(hook, tool_name):
                continue

            hook_result = self._run_handler(hook, context)

            # callable 可返回 PreToolResult 或 dict 或 None
            if isinstance(hook_result, PreToolResult):
                result = hook_result
            elif isinstance(hook_result, dict):
                if hook_result.get("allowed") is False:
                    result.allowed = False
                    result.message = hook_result.get("message", "")
                if hook_result.get("modified_args"):
                    result.modified_args = hook_result["modified_args"]
            elif hook_result is False:
                result.allowed = False
                result.message = f"Blocked by hook: {hook.name}"

            if not result.allowed:
                break  # 有钩子阻止，不再继续

        return result

    def fire_post_tool_use(
        self, tool_name: str, arguments: dict[str, Any], tool_result: str
    ) -> str:
        """触发 PostToolUse 钩子，可修改结果"""
        context = {"tool_name": tool_name, "arguments": arguments, "result": tool_result}

        for hook in self._hooks:
            if hook.hook_type != HookType.POST_TOOL_USE:
                continue
            if not self._matches(hook, tool_name):
                continue

            hook_result = self._run_handler(hook, context)
            if isinstance(hook_result, str) and hook_result:
                tool_result = hook_result  # 替换结果

        return tool_result

    def fire_stop(self) -> None:
        """触发 Stop 钩子"""
        context = {"event": "stop"}
        for hook in self._hooks:
            if hook.hook_type == HookType.STOP:
                self._run_handler(hook, context)

    def fire_subagent_stop(self, agent_id: str, result: str) -> None:
        """触发 SubagentStop 钩子"""
        context = {"event": "subagent_stop", "agent_id": agent_id, "result": result}
        for hook in self._hooks:
            if hook.hook_type == HookType.SUBAGENT_STOP:
                self._run_handler(hook, context)

    def fire_notification(self, message: str, level: str = "info") -> None:
        """触发 Notification 钩子"""
        context = {"event": "notification", "message": message, "level": level}
        for hook in self._hooks:
            if hook.hook_type == HookType.NOTIFICATION:
                self._run_handler(hook, context)

    def fire_pre_compact(self, tokens_before: int) -> None:
        """触发 PreCompact 钩子（上下文压缩前）"""
        context = {"event": "pre_compact", "tokens_before": tokens_before}
        for hook in self._hooks:
            if hook.hook_type == HookType.PRE_COMPACT:
                self._run_handler(hook, context)

    def fire_session_start(self, session_id: str = "") -> None:
        """触发 SessionStart 钩子"""
        context = {"event": "session_start", "session_id": session_id}
        for hook in self._hooks:
            if hook.hook_type == HookType.SESSION_START:
                self._run_handler(hook, context)

    def fire_session_end(self, session_id: str = "") -> None:
        """触发 SessionEnd 钩子"""
        context = {"event": "session_end", "session_id": session_id}
        for hook in self._hooks:
            if hook.hook_type == HookType.SESSION_END:
                self._run_handler(hook, context)

    def fire_user_prompt_submit(self, prompt: str) -> None:
        """触发 UserPromptSubmit 钩子"""
        context = {"event": "user_prompt_submit", "prompt": prompt}
        for hook in self._hooks:
            if hook.hook_type == HookType.USER_PROMPT_SUBMIT:
                self._run_handler(hook, context)

    def list_hooks(self) -> list[dict[str, Any]]:
        """列出所有已注册钩子"""
        return [
            {
                "name": h.name,
                "type": h.hook_type.value,
                "tool_name": h.tool_name,
                "handler_type": "callable" if callable(h.handler) else "shell",
            }
            for h in self._hooks
        ]