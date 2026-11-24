"""atomcode LLM 适配器 — OpenAI 兼容接口（/v1/chat/completions）

独立于 claude-code 复现的 OllamaProvider（/api/chat Anthropic 格式）。
atomcode 用 OpenAI 兼容接口，tool_calls/tool_result 格式不同。
"""
from __future__ import annotations
import json
import time
import requests
from dataclasses import dataclass
from typing import Any


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class LLMResponse:
    content: str
    tool_calls: list[ToolCall]
    done_reason: str
    thinking: str = ""


class OpenAIProvider:
    """ollama /v1/chat/completions 适配器（OpenAI 兼容格式）"""

    def __init__(
        self,
        model: str = "qwen3.8-27b",
        base_url: str = "http://localhost:11434",
        timeout: float = 300.0,
        num_ctx: int = 262144,
        think: bool = True,
    ) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.num_ctx = num_ctx
        self.think = think

    def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        system: str,
    ) -> LLMResponse:
        """调用 ollama /v1/chat/completions"""
        # 组装 OpenAI messages（system 作为第一条消息）
        oai_messages = [{"role": "system", "content": system}] + messages

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": oai_messages,
            "stream": False,
            "max_tokens": 32768,
        }
        if tools:
            payload["tools"] = tools

        url = f"{self.base_url}/v1/chat/completions"
        last_exc = None
        for attempt in range(3):
            try:
                resp = requests.post(url, json=payload, timeout=self.timeout)
                resp.raise_for_status()
                data = resp.json()
                return self._parse_response(data)
            except Exception as e:
                last_exc = e
                time.sleep(1)
        raise last_exc

    def _parse_response(self, data: dict) -> LLMResponse:
        """OpenAI 响应 → LLMResponse"""
        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})
        content = message.get("content") or ""
        thinking = message.get("reasoning_content", "")

        tool_calls = []
        for tc in message.get("tool_calls", []):
            func = tc.get("function", {})
            args_str = func.get("arguments", "{}")
            try:
                args = json.loads(args_str) if isinstance(args_str, str) else args_str
            except json.JSONDecodeError:
                args = {}
            tool_calls.append(ToolCall(
                id=tc.get("id", ""),
                name=func.get("name", ""),
                arguments=args,
            ))

        done_reason = choice.get("finish_reason", "stop")
        return LLMResponse(content=content, tool_calls=tool_calls, done_reason=done_reason, thinking=thinking)