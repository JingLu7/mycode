"""OpenAI 兼容 LLM 适配器 — 通过 /v1/chat/completions 对接 ollama（atomcode 模式用）

与 OllamaProvider（/api/chat，Anthropic 格式）的区别：
- 请求格式：OpenAI 的 tool_calls / role=tool，而非 Anthropic 的 content blocks
- 工具定义：{type: "function", function: {name, description, parameters}}
- 响应格式：choices[0].message.tool_calls，而非 content: [{type: "tool_use"}]
"""
from __future__ import annotations
import json
import time
import requests
from typing import Any

from mycode.llm.provider import LLMResponse, ToolCall


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
        """调用 ollama /v1/chat/completions，返回统一格式的 LLMResponse"""
        oai_messages = self._convert_messages(messages, system)
        oai_tools = self._convert_tools(tools)

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": oai_messages,
            "stream": False,
            "max_tokens": 32768,
        }
        if oai_tools:
            payload["tools"] = oai_tools

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

    def _convert_messages(self, messages: list[dict], system: str) -> list[dict]:
        """Anthropic messages → OpenAI messages"""
        oai: list[dict] = [{"role": "system", "content": system}]

        for msg in messages:
            role = msg.get("role")
            content = msg.get("content")

            # 纯字符串 content → 直接转
            if isinstance(content, str):
                oai.append({"role": role, "content": content})
                continue

            # content 是 list（blocks）
            if isinstance(content, list):
                if role == "assistant":
                    # 提取 text + tool_calls
                    text_parts = []
                    tool_calls = []
                    for block in content:
                        btype = block.get("type")
                        if btype == "text":
                            text_parts.append(block.get("text", ""))
                        elif btype == "thinking":
                            pass  # OpenAI 格式无 thinking block，跳过
                        elif btype == "tool_use":
                            tool_calls.append({
                                "id": block.get("id", ""),
                                "type": "function",
                                "function": {
                                    "name": block.get("name", ""),
                                    "arguments": json.dumps(block.get("input", {}), ensure_ascii=False),
                                },
                            })
                    entry: dict[str, Any] = {"role": "assistant", "content": "\n".join(text_parts) or None}
                    if tool_calls:
                        entry["tool_calls"] = tool_calls
                    oai.append(entry)

                elif role == "user":
                    # 可能含 tool_result
                    for block in content:
                        if block.get("type") == "tool_result":
                            oai.append({
                                "role": "tool",
                                "tool_call_id": block.get("tool_use_id", ""),
                                "content": block.get("content", ""),
                            })
                        elif block.get("type") == "text":
                            oai.append({"role": "user", "content": block.get("text", "")})
        return oai

    def _convert_tools(self, tools: list[dict]) -> list[dict]:
        """Anthropic tool schema → OpenAI function schema"""
        oai_tools = []
        for t in tools:
            oai_tools.append({
                "type": "function",
                "function": {
                    "name": t.get("name", ""),
                    "description": t.get("description", ""),
                    "parameters": t.get("input_schema", {}),
                },
            })
        return oai_tools

    def _parse_response(self, data: dict) -> LLMResponse:
        """OpenAI 响应 → LLMResponse"""
        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})
        content = message.get("content") or ""
        thinking = ""

        # 提取 thinking（ollama 在 OpenAI 兼容模式下可能放 reasoning_content）
        if message.get("reasoning_content"):
            thinking = message["reasoning_content"]

        # 提取 tool_calls
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