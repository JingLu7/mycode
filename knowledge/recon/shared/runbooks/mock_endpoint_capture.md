---
type: Runbook
title: 用 mock 端点抓取 agent CLI 的真实 API 请求
description: 通过 ANTHROPIC_BASE_URL 把 agent CLI 的 API 出口指向记录型 mock 端点，捕获每轮真实请求体（system prompt、工具 schema、参数、headers）。
tags: [task.reverse_engineering, topic.mock_capture, topic.request_protocol]
status: stable
sources: []
created_at: "2026-10-12T00:00:00Z"
updated_at: "2026-10-12T00:00:00Z"
platforms: [agnostic]
---

# 用 mock 端点抓取 agent CLI 的真实 API 请求

## 触发场景

需要逆向 agent CLI（claude-code、codex、atomcode）的 system prompt、工具 schema、请求参数或 agent loop 协议，但目标二进制是编译产物（如 Bun ELF），无法直接读源码。

## 方法

1. 写一个 HTTP mock 端点，监听 `/v1/messages`，把收到的请求体落盘后返回一个合法响应。
2. 用环境变量把 agent CLI 的 API 出口指向 mock：
   ```bash
   ANTHROPIC_BASE_URL=http://127.0.0.1:3456 claude -p "hello"
   ```
3. mock 落盘的 JSON 即包含完整 system prompt、tools 数组、请求参数和 headers。

## 关键约束

- mock 必须返回 **SSE 流式响应**（`text/event-stream`），不能返回非流式 JSON。详见 [SSE 流式响应要求](sse_stream_requirement.md)。
- 起 mock server 和跑 agent CLI 必须在**同一条 bash 命令**内。详见 [沙箱进程清理](sandbox_process_cleanup.md)。
- 关掉精简环境变量才拿完整内容。详见 [环境变量控制内容量](env_var_content_control.md)。

## 验证

- 落盘 JSON 的 `system` 字段非空且长度合理（>1000 字符）。
- `tools` 数组非空，每个工具有 `name`、`input_schema`。
- 请求头包含 `anthropic-version` 和 `anthropic-beta`。