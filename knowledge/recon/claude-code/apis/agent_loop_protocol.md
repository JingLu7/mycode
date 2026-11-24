---
name: agent-loop-protocol
description: claude-code agent loop 的 messages 累积、thinking 保留、tool_result 顺序、cache_control 标记等协议细节
type: concept
domain: recon
route: claude-code
profile: apis
source: artifacts/recon/r3/{parallel,error,thinking,multi}/req-*.json
method: 可编程 SSE mock 驱动 claude agent loop，逐轮捕获请求体
created: 2026-10-13
---

# Agent Loop 协议

claude-code 的 agent loop 通过多轮 `POST /v1/messages` 请求驱动。每轮请求的 `messages` 数组线性累积历史，追加上一轮的 assistant 响应 + tool 执行结果 + 轮次标记。

## messages 累积模式

每轮请求在上一轮基础上追加 **3 条 message**：

```
assistant(tool_use) → user(tool_result) → system(token预算)
```

以 4 轮 multi 场景为例：

| REQ | messages 数 | 新增 |
|-----|------------|------|
| 1 | 2 | user(原始) + system(Environment) |
| 2 | 5 | + assistant[tool_use] + user[tool_result] + system[预算] |
| 3 | 8 | + assistant[tool_use] + user[tool_result] + system[预算] |
| 4 | 11 | + assistant[tool_use] + user[tool_result] + system[预算] |

### 首条 messages 结构

- `[0]` **user**: 原始用户输入（含 2 个 text block：主 prompt + 补充说明）
- `[1]` **system**: 环境信息，内容为 `# Environment\nYou have been invoked in the following environment:\n - Primary working directory: ...\n - Platform: ...\n - Shell: ...`

### 轮次标记 system message

每轮结束后追加的 system message 内容为：

```
<total_tokens>14999980 tokens left</total_tokens>
```

这是 token 预算/轮次边界标记，告知模型剩余 token 预算。

## thinking block 保留

当 assistant 响应包含 thinking block 时，**thinking 在后续请求中被完整保留**在 assistant message 的 content 数组里：

```json
{
  "role": "assistant",
  "content": [
    {"type": "thinking", "thinking": "Let me think about this carefully..."},
    {"type": "tool_use", "id": "toolu_t1", "name": "Bash", "input": {...}}
  ]
}
```

claude 不会 clear thinking。thinking 原样回传，与 Anthropic API 的 extended thinking 协议一致。

## 并行 tool_use 与 tool_result 顺序

assistant 可以在单次响应中返回多个 tool_use block（并行调用）。对应的 tool_result 顺序是**完成顺序**而非调用顺序：

```
assistant: [tool_use(p1), tool_use(p2)]   // 调用顺序 p1 → p2
user: [tool_result(p2), tool_result(p1)]   // 完成顺序 p2 先完成 → p2 在前
```

mycode 实现须注意：tool_result 按实际完成时间排列，不按 tool_use 的 index 排列。

## is_error 标记

工具执行失败时，tool_result 的 `is_error` 设为 `true`，content 为错误描述字符串：

```json
{
  "type": "tool_result",
  "tool_use_id": "toolu_e1",
  "is_error": true,
  "content": "File does not exist. Note: your current working directory is /data/taoming/mycode."
}
```

成功时 `is_error` 为 `false`（或省略）。

## cache_control（prompt caching）

claude 对 system prompt 和轮次标记做 ephemeral cache：

| 位置 | cache_control | 说明 |
|------|---------------|------|
| system[0] | 无 | 系统 prompt 第一段不缓存 |
| system[1] | `{"type": "ephemeral"}` | 第二段标记 ephemeral |
| system[2] | `{"type": "ephemeral"}` | 第三段标记 ephemeral |
| 最新轮次 system msg | `{"type": "ephemeral"}` | 最新 token 预算标记 |

cache_control 打在段的末尾，表示"到此为止的内容可缓存"。system[1] 和 system[2] 的 cache breakpoint 使得多轮请求中 system prompt 段命中缓存、避免重复计费。

## 顶层请求字段

| 字段 | 值 | 说明 |
|------|-----|------|
| model | claude-opus-5-5 | 请求模型 |
| max_tokens | 128000 | 输出上限 |
| stream | true | SSE 流式 |
| temperature | null | 不设（用默认） |
| top_p / top_k | null | 不设 |
| metadata | {user_id: ...} | 含 device_id + session_id |
| stop_sequences | null | 不设 |
| tools | 21 | 工具 schema 数组 |

## stop_reason 观测

| stop_reason | 触发条件 |
|-------------|---------|
| `tool_use` | assistant 返回 tool_use，需执行工具后继续 |
| `end_turn` | assistant 返回 text，对话结束 |

Anthropic API 还定义 `max_tokens`、`stop_sequence`、`pause_turn`，但在 agent loop 主路径中只出现上述两种。

## 实验方法

使用可编程 SSE mock（`tools/recon/mock-loop.mjs`）模拟 Anthropic API，按场景返回不同 SSE 事件序列，驱动 claude 完成完整 agent loop。关键要点：

1. **配置隔离**：`CLAUDE_CONFIG_DIR=/tmp/claude-cfg` 避免 `~/.claude/settings.json` 的 env 段覆盖环境变量
2. **turn 计数**：只对 `POST /v1/messages` 计 turn，忽略 `HEAD /api/hello` 健康检查
3. **端口隔离**：用 `MOCK_PORT` 环境变量避免端口冲突
4. **命令模式**：mock + claude 必须在同一条 shell 命令内执行（沙箱跨命令清理后台进程）