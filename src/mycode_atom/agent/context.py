"""atomcode 上下文管理 — OpenAI messages 格式

与 claude-code（Anthropic 格式）的区别：
- tool_use: assistant 消息的 tool_calls 字段，而非 content blocks
- tool_result: role=tool 消息，而非 role=user + content blocks
"""
from __future__ import annotations
from typing import Any


class Context:
    """管理 OpenAI 格式的对话消息历史"""

    def __init__(self) -> None:
        self.messages: list[dict[str, Any]] = []

    def add_user(self, content: str) -> None:
        self.messages.append({"role": "user", "content": content})

    def add_assistant(self, content: str, tool_calls: list[dict[str, Any]] | None = None, thinking: str = "") -> None:
        """添加 assistant 消息（OpenAI 格式：tool_calls 在顶层字段）"""
        msg: dict[str, Any] = {"role": "assistant", "content": content or None}
        if tool_calls:
            msg["tool_calls"] = tool_calls
        self.messages.append(msg)

    def add_tool_result(self, tool_call_id: str, result: str, is_error: bool = False) -> None:
        """添加工具执行结果（OpenAI 格式：role=tool）"""
        self.messages.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": result,
        })

    def to_list(self) -> list[dict[str, Any]]:
        return self.messages