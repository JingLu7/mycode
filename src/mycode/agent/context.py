"""上下文管理 — 消息历史组装"""
from __future__ import annotations
from typing import Any


class Context:
    """管理对话消息历史"""

    def __init__(self) -> None:
        self.messages: list[dict[str, Any]] = []

    def add_user(self, content: str) -> None:
        self.messages.append({"role": "user", "content": content})

    def add_assistant(self, content: str, tool_calls: list[dict[str, Any]] | None = None, thinking: str = "") -> None:
        """添加 assistant 消息，可附带 thinking 与 tool_use blocks（全量保留，不丢弃）"""
        blocks: list[Any] = []
        if thinking:
            blocks.append({"type": "thinking", "thinking": thinking})
        if content:
            blocks.append({"type": "text", "text": content})
        if tool_calls:
            blocks.extend(tool_calls)
        if len(blocks) == 1 and blocks[0].get("type") == "text":
            self.messages.append({"role": "assistant", "content": blocks[0]["text"]})
        else:
            self.messages.append({"role": "assistant", "content": blocks})

    def add_tool_result(self, tool_use_id: str, result: str, is_error: bool = False) -> None:
        """添加工具执行结果"""
        self.messages.append({
            "role": "user",
            "content": [{
                "type": "tool_result",
                "tool_use_id": tool_use_id,
                "content": result,
                "is_error": is_error,
            }],
        })

    def to_list(self) -> list[dict[str, Any]]:
        return self.messages