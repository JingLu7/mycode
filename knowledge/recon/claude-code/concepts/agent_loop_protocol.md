---
type: Concept
title: claude-code agent loop 消息协议
description: agent 循环每轮发送 5 条 messages（user/system/assistant tool_use/user tool_result/system token预算），含 mid-conversation system turns 和每轮 token 预算注入。
tags: [task.reverse_engineering, topic.agent_loop, topic.request_protocol]
status: stable
sources:
  - resource: artifacts/recon/capture-full-mode.json
    role: evidence
created_at: "2026-10-12T00:00:00Z"
updated_at: "2026-10-12T00:00:00Z"
platforms: [agnostic]
target_versions: ["claude-code@2.1.296"]
---

# claude-code agent loop 消息协议

通过 SSE 流式 mock 驱动 claude-code 走完 tool_use → tool_result 循环，抓到第二轮请求（REQ2）的 messages 结构。

## 5 条 messages 结构

| 序号 | role | 内容 |
|------|------|------|
| 0 | `user` | `[system-reminder(attribution), 用户prompt]` |
| 1 | `system` | `# Environment ...` + output_config（mid-conversation system turn） |
| 2 | `assistant` | `[tool_use Bash id=toolu_1 input={command,description}]` |
| 3 | `user` | `[tool_result id=toolu_1 is_error=False content="..."]` |
| 4 | `system` | `<total_tokens>14999994 tokens left</total_tokens>` |

## 关键发现

### mid-conversation system turns

`system` role 的消息出现在 messages 数组**中间**（序号 1 和 4），不是只在开头。这依赖 `mid-conversation-system-2026-04-07` beta header。

序号 1 的 system turn 注入 `# Environment` 上下文和 `output_config`（effort 级别）。
序号 4 的 system turn 注入 token 预算提醒。

### 每轮 token 预算注入

每轮循环末尾追加一条 system 消息，格式为 `<total_tokens>N tokens left</total_tokens>`，告知模型剩余 token 预算。这是 context management 机制的一部分。

### tool_use → tool_result 配对

assistant turn 的 `tool_use` 有 `id`（如 `toolu_xxx`），user turn 的 `tool_result` 用相同 `id` 回填执行结果。`is_error` 字段标识是否出错。

## 循环推进条件

agent loop 推进需要 mock 正确返回 SSE 流式响应，使 tool_use 进入对话历史。详见 [SSE 流式响应要求](../../shared/runbooks/sse_stream_requirement.md)。