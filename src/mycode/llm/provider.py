"""LLM provider 抽象层"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass
class ToolCall:
    """模型返回的工具调用请求"""
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class LLMResponse:
    """模型响应"""
    content: str
    tool_calls: list[ToolCall]
    done_reason: str
    thinking: str = ""  # thinking 内容（qwen3.8-27b 等支持 thinking 的模型返回）


class LLMProvider(Protocol):
    """LLM provider 协议"""

    def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        system: str,
    ) -> LLMResponse:
        """发送对话请求，返回模型响应"""
        ...