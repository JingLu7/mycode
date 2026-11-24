---
type: API
title: claude-code API 请求参数
description: claude-code 发往 /v1/messages 的顶层请求参数：model、max_tokens、thinking、context_management、output_config、safeguards、stream 等。
tags: [task.reverse_engineering, topic.request_protocol, topic.agent_loop]
status: stable
sources:
  - resource: artifacts/recon/request-skeleton.json
    role: primary
  - resource: artifacts/recon/capture-full-mode.json
    role: evidence
created_at: "2026-10-12T00:00:00Z"
updated_at: "2026-10-12T00:00:00Z"
platforms: [agnostic]
target_versions: ["claude-code@2.1.296"]
---

# claude-code API 请求参数

通过 mock 端点抓取的完整请求顶层参数。

## 参数清单

| 参数 | 值 | 说明 |
|------|-----|------|
| `model` | `claude-opus-5-5` | 模型 ID |
| `max_tokens` | `128000` | 输出 token 上限 |
| `stream` | `true` | 流式响应（必须返回 SSE） |
| `thinking` | `{type: "adaptive", display: "omitted"}` | 自适应思考，不展示思考内容 |
| `context_management` | `{type: "clear_thinking_20251015", keep: "all"}` | 清除思考 token，保留所有消息 |
| `output_config` | `{effort: "medium"}` | 努力级别（low/medium/high） |
| `safeguards` | `[{type: "dangerous_tool_use", classifier_context: {...}}]` | 危险工具使用安全检查 |
| `system` | `[{type: "text", text: "..."}]` | system prompt 数组 |
| `tools` | `[...]` | 工具 schema 数组（20 个） |
| `messages` | `[...]` | 对话消息数组 |

## safeguards.classifier_context

```json
{
  "permission_mode": "default",
  "platform": "linux",
  "additional_directories": []
}
```

`permission_mode` 取值：`default`、`acceptEdits`、`plan`、`bypassPermissions`。

## 与 beta headers 的关系

`thinking`、`context_management`、`output_config`、`safeguards` 等参数依赖对应的 beta header 启用。详见 [beta headers](beta_headers.md)。