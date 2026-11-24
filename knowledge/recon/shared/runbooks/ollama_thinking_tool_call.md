---
type: Runbook
title: ollama qwen3-32b 必须关 thinking 才返回 tool_calls
description: ollama 0.34.x 的 qwen3-32b 在默认 thinking 模式下，thinking 内容吃光 num_predict 预算，导致 done_reason=length 且不返回 tool_calls；必须显式设置 think:false。
tags: [task.debugging, topic.ollama, topic.tool_system]
status: stable
sources: []
created_at: "2026-10-12T00:00:00Z"
updated_at: "2026-10-12T00:00:00Z"
platforms: [agnostic]
---

# ollama thinking 模式与 tool calling 冲突

## 症状

用 ollama 0.34.3 运行 `qwen3-32b:latest`，发送带 tools 的 chat 请求。模型返回 `done_reason: "length"`，`message.tool_calls` 为 null 或缺失。增大 `num_predict` 也无效（thinking 内容无限膨胀）。

## 根因

qwen3-32b 默认开启 thinking 模式，模型先输出 `<think>...</think>` 推理内容。thinking token 计入 `num_predict` 预算，吃光后截断，来不及输出 tool_calls 的 JSON。

## 处置

请求时显式关闭 thinking：

```bash
curl http://localhost:11434/api/chat -d '{
  "model": "qwen3-32b",
  "messages": [...],
  "tools": [...],
  "think": false,
  "stream": false
}'
```

关键参数：`"think": false`。

## 返回格式

关闭 thinking 后，tool_calls 正常返回：

```json
{
  "message": {
    "role": "assistant",
    "content": "",
    "tool_calls": [
      {
        "id": "call_xxx",
        "function": {
          "index": 0,
          "name": "tool_name",
          "arguments": "{\"key\":\"value\"}"
        }
      }
    ]
  },
  "done_reason": "stop"
}
```

## 验证

- `done_reason` 为 `"stop"` 而非 `"length"`。
- `message.tool_calls` 非空，`function.name` 和 `function.arguments` 有值。