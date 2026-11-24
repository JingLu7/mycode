---
type: API
title: claude-code beta headers 清单
description: claude-code 请求携带的 anthropic-beta headers，启用 interleaved-thinking、context-management、mid-conversation-system、effort、dangerous-tool-use 等特性。
tags: [task.reverse_engineering, topic.request_protocol, topic.harness]
status: stable
sources:
  - resource: artifacts/recon/request-headers.json
    role: primary
created_at: "2026-10-12T00:00:00Z"
updated_at: "2026-10-12T00:00:00Z"
platforms: [agnostic]
target_versions: ["claude-code@2.1.296"]
---

# claude-code beta headers 清单

请求头 `anthropic-beta` 携带的特性开关（逗号分隔）：

| beta header | 启用特性 |
|-------------|---------|
| `claude-code-20250219` | claude-code 专属行为 |
| `interleaved-thinking-2025-05-14` | 交错思考（thinking 与 content 交替） |
| `thinking-token-count-2026-05-13` | thinking token 计数 |
| `context-management-2025-06-27` | 上下文管理（自动摘要、清除 thinking） |
| `prompt-caching-scope-2026-01-05` | prompt 缓存作用域 |
| `mid-conversation-system-2026-04-07` | mid-conversation system turns |
| `per-turn-control-2026-07-01` | 每轮控制 |
| `mid-conversation-tool-changes-2026-07-01` | mid-conversation 工具变更 |
| `effort-2025-11-24` | effort 级别控制 |
| `dangerous-tool-use-2026-09-03` | 危险工具使用安全检查 |
| `afk-mode-2026-01-31` | AFK 模式 |

## 其他关键 headers

| header | 值 |
|--------|-----|
| `anthropic-version` | `2023-06-01` |
| `content-type` | `application/json` |
| `x-api-key` | （API key） |
| `user-agent` | `claude-cli/2.1.296 ...` |