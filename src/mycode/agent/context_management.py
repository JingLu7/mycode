"""Context management — token 计数与自动摘要"""
from __future__ import annotations
from typing import Any


def estimate_tokens(text: str) -> int:
    """粗略估算 token 数（英文 ~4 字符/token，中文 ~2 字符/token）"""
    return max(1, len(text) // 3)


def estimate_messages_tokens(messages: list[dict[str, Any]]) -> int:
    """估算 messages 列表的总 token 数"""
    total = 0
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, str):
            total += estimate_tokens(content)
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    total += estimate_tokens(block.get("text", ""))
                    total += estimate_tokens(str(block.get("input", "")))
                    total += estimate_tokens(str(block.get("content", "")))
                elif isinstance(block, str):
                    total += estimate_tokens(block)
    return total


def summarize_old_messages(
    messages: list[dict[str, Any]],
    max_tokens: int = 30000,
    keep_recent: int = 10,
) -> list[dict[str, Any]]:
    """当 token 超过上限时，把旧消息摘要为一条 system 消息

    策略：
    - 保留最近 keep_recent 条消息不动
    - 把更早的消息替换为一条 system 消息，列出已完成的工具调用摘要
    """
    total = estimate_messages_tokens(messages)
    if total <= max_tokens or len(messages) <= keep_recent:
        return messages

    old_messages = messages[:-keep_recent]
    recent_messages = messages[-keep_recent:]

    # 构建摘要
    summary_parts: list[str] = ["[Context summary — earlier conversation was compressed]"]
    for msg in old_messages:
        role = msg.get("role", "?")
        content = msg.get("content", "")
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    btype = block.get("type", "")
                    if btype == "text" and block.get("text"):
                        text = block["text"][:150]
                        summary_parts.append(f"  {role}: {text}...")
                    elif btype == "tool_use":
                        summary_parts.append(f"  {role} called {block.get('name', '?')}")
                    elif btype == "tool_result":
                        result = str(block.get("content", ""))[:100]
                        summary_parts.append(f"  tool_result: {result}...")
        elif isinstance(content, str) and content:
            summary_parts.append(f"  {role}: {content[:150]}...")

    summary_msg = {
        "role": "system",
        "content": "\n".join(summary_parts),
    }

    return [summary_msg] + recent_messages

def clear_thinking(messages: list[dict[str, Any]], keep_recent: int = 1) -> list[dict[str, Any]]:
    """清除旧消息中的 thinking block（对齐 claude-code 的 clear_thinking_20251015）。

    保留最近 keep_recent 条消息的 thinking，更早的 thinking block 移除以节省 token。
    返回新列表，不修改原列表。
    """
    n = len(messages)
    out: list[dict[str, Any]] = []
    for idx, msg in enumerate(messages):
        content = msg.get("content")
        if idx < n - keep_recent and isinstance(content, list):
            filtered = [
                b for b in content
                if not (isinstance(b, dict) and b.get("type") == "thinking")
            ]
            filtered = filtered or content  # 若全是 thinking，保留原样避免空消息
            msg = {**msg, "content": filtered}
        out.append(msg)
    return out