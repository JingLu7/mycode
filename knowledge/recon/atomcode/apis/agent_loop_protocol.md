---
type: API
title: atomcode 的 agent loop 协议
description: 通过驱动 mock 返回 tool_use，捕获 atomcode 完整 agent loop（请求→tool_use→执行→tool_result→最终响应），确认使用 OpenAI 格式的 tool_calls/tool_result 协议。
tags: [task.reverse_engineering, topic.agent_loop, topic.api]
status: stable
sources:
  - resource: artifacts/recon/atomcode/loop-req-01.json
    role: evidence
  - resource: artifacts/recon/atomcode/loop-req-03.json
    role: evidence
created_at: "2026-10-23T00:00:00Z"
updated_at: "2026-10-23T00:00:00Z"
platforms: [agnostic]
target_versions: ["atomcode@2026-10-23"]
---

# atomcode 的 agent loop 协议

## 完整循环（3 个请求）

### REQ-01：首轮请求

```
messages:
  [0] system (36810 chars) — 完整 system prompt
  [1] user: "read /etc/hostname"
  [2] user: <system-reminder> Before you explore the codebase...
  [3] user: <system-reminder> Current date: 2026-10-23 (Fri)
```

mock 返回 `tool_calls: [read_file(/etc/hostname)]`

### REQ-02：标题生成（并行）

```
messages:
  [0] system (218 chars) — 标题生成 prompt
  [1] user: "read /etc/hostname"
```

与主请求并行，用于给会话起标题。

### REQ-03：tool_result 回填后

```
messages:
  [0] system (36810 chars)
  [1] user: "read /etc/hostname"
  [2] assistant tool_calls: [read_file]        ← 模型上一轮的 tool_use
  [3] tool_result (call_id=call_recon_01)      ← atomcode 执行后的结果
  [4] user: <system-reminder> Current date...
```

mock 返回最终文本 "Done. I read the file."

## OpenAI 格式协议

| 环节 | 格式 |
|------|------|
| tool_use | `assistant` 消息的 `tool_calls` 字段：`[{id, function: {name, arguments}}]` |
| tool_result | 独立 `role: "tool"` 消息：`{tool_call_id, content}` |
| 流式 | SSE `text/event-stream`，`choices[0].delta.tool_calls` |

### 与 Anthropic 格式对比

| 维度 | claude-code (Anthropic) | atomcode (OpenAI) |
|------|------------------------|-------------------|
| tool_use | `content: [{type: "tool_use", id, name, input}]` | `tool_calls: [{id, function: {name, arguments}}]` |
| tool_result | `role: "user", content: [{type: "tool_result", tool_use_id, content}]` | `role: "tool", {tool_call_id, content}` |
| 参数格式 | `input` (object) | `arguments` (JSON string) |

## 沙箱限制

atomcode 执行 `read_file /etc/hostname` 时返回：
```
read_file: /etc/hostname is outside the world's root /data/taoming
```

说明 atomcode 有**工作目录沙箱**——文件访问被限制在 cwd（`/data/taoming`）内。

## system-reminder 机制

atomcode 在 user 消息中注入 `<system-reminder>`：
1. **探索前提醒**：在首轮注入 "Before you explore the codebase, plan, or propose a solution..."
2. **日期提醒**：每轮注入 "Current date: 2026-10-23 (Fri)"

与 claude-code 的 system-reminder 机制类似，但内容不同。