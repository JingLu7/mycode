# Claude Code Harness 逆向工程报告

> 逆向目标：`@anthropic-ai/claude-code@2.1.296`
> 逆向时间：2026-10-12
> 方法路线：A（静态字符串）+ B（动态请求抓取）+ D（白盒契约）
> 产出位置：`artifacts/recon/`

## 1. 概述

本报告系统梳理 claude-code@2.1.296 的 harness 结构与 agent 工作流设计，作为 mycode 开发的设计参照。

### 逆向目标

| 属性 | 值 |
|------|-----|
| 包名 | `@anthropic-ai/claude-code` |
| 版本 | 2.1.296 |
| 安装路径 | `/home/zigaa/.local/lib/node_modules/@anthropic-ai/claude-code/` |
| 主二进制 | `bin/claude.exe`（246MB ELF） |
| 类型声明 | `sdk-tools.d.ts`（171KB，43 工具契约） |

### 方法路线

| 路线 | 方法 | 产出 | 状态 |
|------|------|------|------|
| A | `strings` 静态提取 | 碎片化 prompt、环境变量名 | 完成 |
| B | mock 端点 + `ANTHROPIC_BASE_URL` 动态抓取 | 完整 system prompt + tools + 参数 + headers + agent loop | 完成 |
| C | ELF 反编译 | Bun runtime + JSC 引擎（无应用逻辑） | 跳过（价值有限） |
| D | `sdk-tools.d.ts` 白盒契约 | 43 工具 TypeScript 类型定义 | 完成（交叉验证） |

## 2. 物理结构

`bin/claude.exe` 是 **Bun `--compile` 产出的原生 ELF 单文件**，不是 JS bundle。

| 属性 | 值 |
|------|-----|
| 格式 | ELF 64-bit LSB executable, x86-64 |
| 大小 | 246 MB |
| stripped | no（仅动态符号表 ~1230 项） |
| 特殊段 | `.bun_builtins` |
| 运行时 | Bun runtime + JavaScriptCore (JSC) 引擎 |

**应用代码嵌入方式**：JS 以 JSC bytecode 内嵌，非明文源码。反编译 `.text` 段只能得到 Bun/JSC 的 C++ 代码，拿不到应用层逻辑。

**可提取的明文资产**：
- 字符串常量：`strings bin/claude.exe` → system prompt 片段、工具名、`CLAUDE_CODE_*` 环境变量名
- 类型声明：`sdk-tools.d.ts` → 43 个工具的 TypeScript 接口定义

## 3. API 请求结构

### 3.1 端点与 Headers

claude-code 向 `${ANTHROPIC_BASE_URL}/v1/messages` 发送 POST 请求。

关键 headers：

| header | 值 | 说明 |
|--------|-----|------|
| `anthropic-version` | `2023-06-01` | API 版本 |
| `anthropic-beta` | （见下表） | 11 个 beta 特性开关 |
| `content-type` | `application/json` | |
| `user-agent` | `claude-cli/2.1.296 (external, sdk-cli)` | |
| `x-api-key` | （API key） | |
| `x-stainless-runtime` | `node` | SDK 运行时 |
| `x-stainless-runtime-version` | `v26.3.0` | Node 版本 |

### 3.2 Beta Headers

`anthropic-beta` 携带的 11 个特性开关（逗号分隔）：

| beta header | 启用特性 |
|-------------|---------|
| `claude-code-20250219` | claude-code 专属行为 |
| `interleaved-thinking-2025-05-14` | 交错思考 |
| `thinking-token-count-2026-05-13` | thinking token 计数 |
| `context-management-2025-06-27` | 上下文管理（自动摘要、清除 thinking） |
| `prompt-caching-scope-2026-01-05` | prompt 缓存作用域 |
| `mid-conversation-system-2026-04-07` | mid-conversation system turns |
| `per-turn-control-2026-07-01` | 每轮控制 |
| `mid-conversation-tool-changes-2026-07-01` | mid-conversation 工具变更 |
| `effort-2025-11-24` | effort 级别控制 |
| `dangerous-tool-use-2026-09-03` | 危险工具使用安全检查 |
| `afk-mode-2026-01-31` | AFK 模式 |

### 3.3 顶层请求参数

```json
{
  "model": "claude-opus-5-5",
  "max_tokens": 128000,
  "stream": true,
  "thinking": {"type": "adaptive", "display": "omitted"},
  "context_management": {"edits": [{"type": "clear_thinking_20251015", "keep": "all"}]},
  "output_config": {"effort": "medium"},
  "safeguards": [{"type": "dangerous_tool_use", "classifier_context": {...}}],
  "system": [{"type": "text", "text": "..."}],
  "tools": [...],
  "messages": [...]
}
```

| 参数 | 值 | 说明 |
|------|-----|------|
| `model` | `claude-opus-5-5` | 模型 ID |
| `max_tokens` | `128000` | 输出 token 上限 |
| `stream` | `true` | 流式响应（SSE） |
| `thinking` | `{type: "adaptive", display: "omitted"}` | 自适应思考，不展示 |
| `context_management` | `{type: "clear_thinking_20251015", keep: "all"}` | 清除 thinking token |
| `output_config` | `{effort: "medium"}` | 努力级别 |
| `safeguards` | `[{type: "dangerous_tool_use", ...}]` | 危险工具安全检查 |

`safeguards[0].classifier_context` 包含权限模式、平台、工作目录、git 状态等上下文，供安全分类器判断工具调用是否危险。

## 4. System Prompt 分段设计

完整 system prompt 约 5770 字符，分 11 段：

| 序号 | 标题 | 内容摘要 |
|------|------|---------|
| 1 | billing header | `x-anthropic-billing-header: cc_version=2.1.296.406; cc_entrypoint=sdk-cli;` |
| 2 | agent 身份 | "You are a Claude agent, built on Anthropic's Claude Agent SDK." |
| 3 | 安全策略 | 授权安全测试、防御性安全、CTF、教育场景；拒绝破坏性技术 |
| 4 | `# Harness` | 权限模式、mid-conversation system turns、hooks、文件工具优先、并行、代码引用 |
| 5 | 代码风格 | "Write code that reads like the surrounding code" |
| 6 | 代词 | they/them 中性代词 |
| 7 | 不可逆操作 | 确认后才执行；如实报告结果 |
| 8 | `# Session-specific guidance` | skills 加载（`/<skill-name>`） |
| 9 | `# Memory` | 文件记忆系统：frontmatter + MEMORY.md 索引 |
| 10 | `# Environment` | 模型 ID 清单、Claude Code 可用形态、Fast mode |
| 11 | `# Context management` | 自动摘要、token 预算 |

### 关键段详解

**`# Harness`**（第 4 段）定义了 agent 的操作约束：
- 工具在用户选择的权限模式下运行；被拒绝的调用不重试
- mid-conversation system turns 可更新规则；hooks 可拦截工具调用
- 优先使用专用文件/搜索工具而非 shell
- 独立工具调用可并行
- 代码引用格式：`file_path:line_number`

**`# Memory`**（第 9 段）定义了文件记忆系统：
- 每条记忆一个文件，带 YAML frontmatter（name/description/metadata.type）
- 类型：`user`（用户画像）、`feedback`（工作指导）、`project`（项目上下文）、`reference`（外部资源）
- `MEMORY.md` 作为索引，每条记忆一行指针
- 写前检查是否已有覆盖；不保存代码结构、git 历史、会话临时状态

**`# Context management`**（第 11 段）定义了上下文管理：
- 对话过长时自动摘要
- 摘要 + 剩余未摘要内容放入下一个上下文窗口
- 末尾注入 `<total_tokens>N tokens left</total_tokens>`

## 5. 工具系统

### 5.1 非交互模式（`-p`）捕获的 20 个工具

| 工具 | 必选参数 | 可选参数 | 类别 |
|------|---------|---------|------|
| `Bash` | `command` | `timeout`, `description`, `run_in_background`, `dangerouslyDisableSandbox` | 执行 |
| `Read` | `file_path` | `offset`, `limit`, `pages`, `allow_large` | 文件 |
| `Write` | `file_path`, `content` | — | 文件 |
| `Edit` | `file_path`, `old_string`, `new_string` | `replace_all` | 文件 |
| `NotebookEdit` | `notebook_path`, `new_source` | `cell_id`, `cell_type`, `edit_mode` | 文件 |
| `Agent` | `description`, `prompt` | `subagent_type`, `model`, `effort`, `run_in_background`, `isolation` | 子 agent |
| `ListAgents` | — | `channel`, `q` | 子 agent |
| `WebFetch` | `url`, `prompt` | `offset` | 网络 |
| `WebSearch` | `query` | `allowed_domains`, `blocked_domains` | 网络 |
| `Skill` | `skill` | `args` | 元 |
| `Workflow` | — | `script`, `name`, `description`, `title`, `args`, `scriptPath`, `resumeFromRunId` | 元 |
| `CronCreate` | `cron`, `prompt` | `recurring`, `durable` | 调度 |
| `CronDelete` | `id` | — | 调度 |
| `CronList` | — | — | 调度 |
| `ScheduleWakeup` | — | `delaySeconds`, `reason`, `prompt`, `stop`, `noop` | 调度 |
| `EnterWorktree` | — | `name`, `path` | git |
| `ExitWorktree` | `action` | `discard_changes` | git |
| `SendMessage` | `to`, `message` | `summary`, `notify_when_idle` | 通信 |
| `ReportFindings` | `findings` | `level` | 通信 |
| `TaskStop` | — | `task_id`, `shell_id` | 控制 |

### 5.2 与 sdk-tools.d.ts 的差异

`sdk-tools.d.ts` 声明 43 个工具契约，非交互模式只捕获到 20 个。其余可能需要交互式 TUI、`--plan` flag、特定权限模式或特定 session 状态激活。

### 5.3 工具 schema 结构

每个工具的 `input_schema` 是标准 JSON Schema：
```json
{
  "name": "Bash",
  "description": "...",
  "input_schema": {
    "type": "object",
    "properties": {...},
    "required": [...]
  }
}
```

## 6. Agent Loop 协议

通过 SSE 流式 mock 驱动 claude-code 走完 tool_use → tool_result 循环，抓到第二轮请求（REQ2）的 messages 结构。

### 6.1 消息结构

每轮请求的 `messages` 数组结构：

| 序号 | role | 内容 |
|------|------|------|
| 0 | `user` | `[system-reminder(attribution), 用户prompt]` |
| 1 | `system` | `# Environment ...` + `output_config`（mid-conversation system turn） |
| 2 | `assistant` | `[tool_use Bash id=toolu_1 input={command,description}]` |
| 3 | `user` | `[tool_result id=toolu_1 is_error=False content="..."]` |
| 4 | `system` | `<total_tokens>14999994 tokens left</total_tokens>` |

### 6.2 关键发现

**mid-conversation system turns**：`system` role 消息出现在 messages 数组中间（序号 1 和 4），依赖 `mid-conversation-system-2026-04-07` beta header。序号 1 注入环境上下文和 effort 级别；序号 4 注入 token 预算提醒。

**每轮 token 预算注入**：每轮循环末尾追加 system 消息 `<total_tokens>N tokens left</total_tokens>`，是 context management 机制的一部分。

**tool_use → tool_result 配对**：assistant turn 的 `tool_use` 有 `id`，user turn 的 `tool_result` 用相同 `id` 回填执行结果，`is_error` 标识是否出错。

**流式响应**：claude-code 发送 `stream: true`，API 返回 SSE 流。mock 必须返回 `text/event-stream`，否则 tool_use 不会进入对话历史。

### 6.3 循环图

```
用户 prompt
    │
    ▼
组装 messages = [user(prompt)]
    │
    ▼
POST /v1/messages (system + tools + messages) ──→ API
    │                                                    │
    ▼                                                    │
解析 SSE 流                                             │
    │                                                    │
    ├── text content → 输出给用户                         │
    │                                                    │
    ├── tool_use → 执行工具 → tool_result 加入 messages   │
    │                    │                                │
    │                    └── 回到 POST ──────────────────┘
    │
    └── stop_reason: "end_turn" → 结束
```

## 7. 逆向方法总结

### 7.1 B 路线（动态抓取）操作步骤

1. 写 mock HTTP 端点监听 `/v1/messages`，落盘请求体后返回合法 SSE 流
2. `ANTHROPIC_BASE_URL=http://127.0.0.1:PORT` 把 claude 出口指向 mock
3. `unset CLAUDE_CODE_SIMPLE`（否则内容被精简）
4. 同一条 bash 命令内起 server + 跑 claude（沙箱清理跨命令后台进程）
5. mock 落盘的 JSON 即完整请求

### 7.2 踩过的三个坑

| 坑 | 症状 | 根因 | 处置 |
|----|------|------|------|
| 沙箱进程清理 | server 启动后跑 claude 报 ECONNREFUSED | 沙箱清理跨命令后台进程 | 同命令内起 server + 跑 CLI |
| 内容精简 | system prompt 仅 500 字符 | `CLAUDE_CODE_SIMPLE=1` | unset 该变量 |
| tool_use 丢失 | REQ2 与 REQ1 完全相同 | mock 返回非流式 JSON，SSE 解析器无法提取 | mock 返回 `text/event-stream` SSE 流 |

### 7.3 驱动 agent loop 的方法

用可编程 mock 注入 `tool_use` 响应 → claude 执行工具 → 回填 `tool_result` → claude 发起下一轮请求。mock 需要按 SSE 事件序列返回：

```
message_start → content_block_start → content_block_delta(input_json_delta) → content_block_stop → message_delta → message_stop
```

## 8. 对 mycode 设计的启示

### 8.1 架构形态

mycode 贴近 claude-code 原栈，复用其设计模式：

| claude-code 设计 | mycode 对应 |
|------------------|------------|
| system prompt 11 段 | 复用分段结构，裁剪 billing/代词等段 |
| 20 工具 | P0 先实现 Bash/Read/Write 3 个 |
| agent loop 5 messages | 复用消息结构，简化 mid-conversation system turns |
| 请求参数 | 简化：去掉 thinking/safeguards，保留 model/max_tokens/stream |
| beta headers | ollama 不需要 beta headers |

### 8.2 P0 范围

- **agent loop**：user prompt → LLM → tool_use → 执行 → tool_result → LLM → end
- **3 工具**：Bash（执行命令）、Read（读文件）、Write（写文件）
- **LLM**：ollama `/api/chat`，`think: false`
- **CLI**：`python -m mycode "用户 prompt"`

### 8.3 后续扩展方向

- P1：harness 核心（权限、memory、context management）
- P2：更多工具（Edit/Glob/Grep/WebFetch）、subagent、hooks
- 远期：逆向 codex/atomcode，对比设计差异