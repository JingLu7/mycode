"""ollama 适配器 — 通过 /api/chat 对接本地 ollama"""
from __future__ import annotations
import json
import time
import requests
from typing import Any

from mycode.llm.provider import LLMProvider, LLMResponse, ToolCall


class OllamaProvider:
    """ollama /api/chat 适配器"""

    def __init__(
        self,
        model: str = "qwen3-32b",
        base_url: str = "http://localhost:11434",
        timeout: float = 300.0,
        num_ctx: int = 32768,
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
        """调用 ollama /api/chat，返回统一格式的响应"""
        # 组装 ollama 请求
        # ollama 的 messages 格式与 Anthropic 不同：
        # - system 作为独立字段
        # - tool_result 作为 user role 的 content
        ollama_messages = self._convert_messages(messages, system)
        ollama_tools = self._convert_tools(tools)

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": ollama_messages,
            "stream": False,
            "think": self.think,
            "options": {"num_ctx": self.num_ctx},
        }
        # cache_control：对齐 claude-code 的 ephemeral 标记。
        # ollama 0.34.3 的 /api/chat 格式为简单 role/content 数组，
        # 无 block 结构，故 cache_control 字段在 ollama 层面暂不支持。
        # 保留字段以便未来 ollama 支持时自动生效。
        # 当前 system prompt 中已包含 cache_control 说明（作为文档）。
        if ollama_tools:
            payload["tools"] = ollama_tools

        # 沙箱内 ollama 间歇性中断（/api/tags 200 但 /api/chat 被拒），重试 3 次
        last_exc = None
        for attempt in range(3):
            try:
                resp = requests.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                    timeout=self.timeout,
                )
                resp.raise_for_status()
                data = resp.json()
                break
            except requests.RequestException as e:
                last_exc = e
                if attempt < 2:
                    time.sleep(1.0 * (attempt + 1))
        else:
            raise last_exc  # type: ignore[misc]

        return self._parse_response(data)

    def _convert_messages(
        self, messages: list[dict[str, Any]], system: str
    ) -> list[dict[str, Any]]:
        """把 Anthropic 格式的 messages 转为 ollama 格式。

        全量保留：thinking / tool_use（→ ollama tool_calls）/ tool_result（→ role:tool），
        不丢弃任何消息块（修复此前 pass 掉 tool_use 的弱点）。
        """
        result: list[dict[str, Any]] = []

        # ollama 用独立 system 字段，不放在 messages 里
        # 但我们在调用时把 system 作为第一条 system message
        if system:
            result.append({"role": "system", "content": system})

        for msg in messages:
            role = msg["role"]
            content = msg.get("content", "")

            # Anthropic content 可以是 string 或 list of blocks
            if isinstance(content, list):
                text_parts: list[str] = []
                thinking = ""
                tool_calls: list[dict[str, Any]] = []
                tool_result_msgs: list[dict[str, Any]] = []
                for block in content:
                    if isinstance(block, str):
                        text_parts.append(block)
                    elif isinstance(block, dict):
                        btype = block.get("type")
                        if btype == "text":
                            text_parts.append(block.get("text", ""))
                        elif btype == "thinking":
                            thinking = block.get("thinking", "")
                        elif btype == "tool_use":
                            # 全量保留 assistant 的 tool_use → ollama tool_calls
                            tool_calls.append({
                                "function": {
                                    "name": block.get("name", ""),
                                    "arguments": block.get("input", {}),
                                }
                            })
                        elif btype == "tool_result":
                            # tool_result → ollama role:tool 消息
                            tool_content = block.get("content", "")
                            if isinstance(tool_content, list):
                                tool_content = "\n".join(
                                    b.get("text", "") for b in tool_content if isinstance(b, dict)
                                )
                            tool_result_msgs.append({
                                "role": "tool",
                                "content": str(tool_content),
                            })

                if tool_calls or thinking:
                    # assistant 消息：保留 thinking + tool_calls
                    am: dict[str, Any] = {"role": "assistant", "content": "\n".join(text_parts)}
                    if thinking:
                        am["thinking"] = thinking
                    if tool_calls:
                        am["tool_calls"] = tool_calls
                    result.append(am)
                elif text_parts:
                    result.append({"role": role, "content": "\n".join(text_parts)})

                result.extend(tool_result_msgs)
            elif isinstance(content, str) and content:
                result.append({"role": role, "content": content})

        return result

    def _convert_tools(self, tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Anthropic tools 格式转 ollama tools 格式"""
        ollama_tools = []
        for t in tools:
            if "function" in t:
                # 已经是 ollama 格式
                ollama_tools.append(t)
            else:
                # Anthropic 格式 → ollama 格式
                ollama_tools.append({
                    "type": "function",
                    "function": {
                        "name": t["name"],
                        "description": t.get("description", ""),
                        "parameters": t.get("input_schema", {}),
                    },
                })
        return ollama_tools

    def _parse_response(self, data: dict[str, Any]) -> LLMResponse:
        """解析 ollama 响应为统一格式"""
        message = data.get("message", {})
        content = message.get("content", "")
        thinking = message.get("thinking", "") or ""
        done_reason = data.get("done_reason", "stop")

        tool_calls: list[ToolCall] = []
        for tc in message.get("tool_calls", []) or []:
            func = tc.get("function", {})
            args_str = func.get("arguments", "{}")
            if isinstance(args_str, str):
                try:
                    args = json.loads(args_str)
                except json.JSONDecodeError:
                    args = {"_raw": args_str}
            else:
                args = args_str
            tool_calls.append(ToolCall(
                id=tc.get("id", f"call_{len(tool_calls)}"),
                name=func.get("name", ""),
                arguments=args,
            ))

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            done_reason=done_reason,
            thinking=thinking,
        )