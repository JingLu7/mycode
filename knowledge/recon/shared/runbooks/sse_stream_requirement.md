---
type: Runbook
title: agent CLI 要求 SSE 流式响应，非流式 tool_use 会被丢弃
description: claude-code 发送 stream:true 请求，mock 端点必须返回 text/event-stream SSE 流；返回非流式 JSON 时 tool_use 内容不会进入对话历史。
tags: [task.reverse_engineering, topic.sse_streaming, topic.agent_loop]
status: stable
sources: []
created_at: "2026-10-12T00:00:00Z"
updated_at: "2026-10-12T00:00:00Z"
platforms: [agnostic]
---

# SSE 流式响应要求

## 症状

mock 端点返回标准非流式 JSON 响应（`application/json`），包含 `tool_use` content block。agent CLI 发起第二轮请求（REQ2）时，**REQ2 的 messages 与 REQ1 完全相同**——tool_use 没有进入对话历史，agent loop 卡在第一步。

## 根因

claude-code 发送 `"stream": true`。当 mock 返回非流式 JSON 时，claude-code 的 SSE 解析器无法从中提取 content blocks，tool_use 被静默丢弃。

## 处置

mock 必须返回 `Content-Type: text/event-stream` 的 SSE 流。事件序列：

```
event: message_start
data: {"type":"message_start","message":{"id":"msg_xxx","type":"message","role":"assistant","content":[],"model":"...","stop_reason":null,"usage":{"input_tokens":1,"output_tokens":1}}}

event: content_block_start
data: {"type":"content_block_start","index":0,"content_block":{"type":"tool_use","id":"toolu_xxx","name":"Bash","input":{}}}

event: content_block_delta
data: {"type":"content_block_delta","index":0,"delta":{"type":"input_json_delta","partial_json":"{\"command\":\"echo hello\",\"description\":\"test\"}"}}

event: content_block_stop
data: {"type":"content_block_stop","index":0}

event: message_delta
data: {"type":"message_delta","delta":{"stop_reason":"tool_use"},"usage":{"output_tokens":10}}

event: message_stop
data: {"type":"message_stop"}
```

每个 `data:` 行的 JSON 必须是完整 JSON 对象。`input_json_delta` 的 `partial_json` 可以分多次发送，也可以一次发完整。

## 验证

- REQ2 的 messages 数组长度 > REQ1，包含 assistant turn（tool_use）和 user turn（tool_result）。
- agent loop 正常推进，不再卡在第一步。