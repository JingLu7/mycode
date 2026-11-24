# AtomCode 逆向工程报告

> 日期：2026-10-23 | 目标：atomcode（`/home/zigaa/.local/bin/atomcode`）| 方法：B 路线（mock 端点抓取）

## 1. 目标基本信息

| 属性 | 值 |
|------|-----|
| 二进制 | ELF 64-bit LSB PIE executable, x86-64 |
| 大小 | 46 MB |
| stripped | yes |
| 运行时 | C/C++ 原生编译（非 Bun/JS） |
| 配置 | `~/.atomcode/config.toml`（TOML） |
| API | OpenAI 兼容 `/v1/chat/completions` |
| 默认 provider | AtomGit（`https://llm-api.atomgit.com/v1`） |
| 默认模型 | qwen3.8-27b |
| 会话恢复 | `--continue` / `--resume <id>` |
| 子命令 | login/status/resume/review/mcp/daemon/webui/plugin/hooks/schedule/setup |

## 2. B 路线抓取方法

1. 写 mock 端点（`tools/recon/mock-atomcode.mjs`），监听 OpenAI 格式 `/v1/chat/completions`
2. 创建临时 config.toml，base_url 指向 `http://127.0.0.1:3456/v1`
3. `HOME=/tmp/atomcode-home` 重定向数据目录（绕过沙箱只读）
4. 单条命令：起 mock + 跑 `atomcode --config <mock> -p "hello" --dev [--no-tools]`
5. mock 落盘请求体到 `artifacts/recon/atomcode/`

## 3. system prompt 结构（22 段，36810 字符）

| # | 段 | 字符 | 核心内容 |
|---|-----|------|---------|
| 0 | 身份定义 | 719 | "You are AtomCode, an AI coding agent by AtomGit..." |
| 1 | PRECEDENCE | 659 | 优先级规则 |
| 2 | CONTENT SAFETY | 2299 | 内容安全 |
| 3 | SYSTEM REMINDERS | 595 | 系统提醒机制 |
| 4 | MCP SERVER | 687 | MCP 服务器指令 |
| 5 | CONTEXT MANAGEMENT | 410 | 自动上下文压缩（不告诉用户"上下文不够"） |
| 6 | WORKFLOW | 2221 | 简单→直接做；非平凡→UNDERSTAND→SEARCH→PLAN→EDIT→VERIFY→SUMMARIZE；Bug→REPRODUCE→DIAGNOSE→FIX→VERIFY |
| 7 | TOOLS | 3222 | 工具使用说明 |
| 8 | DOING TASKS | 1400 | 任务执行 |
| 9 | WHEN COMMANDS FAIL | 667 | 命令失败处理 |
| 10 | RISKY ACTIONS | 525 | 危险操作 |
| 11 | SCOPE | 408 | 范围 |
| 12 | OPENING FILES | 493 | 打开文件 |
| 13 | PROGRESS SIGNPOSTS | 1586 | 进度标记 |
| 14 | OUTPUT | 508 | 输出 |
| 15 | CONTENT-TRANSFORMATION | 1343 | 内容转换 |
| 16 | CHINESE CODE SUPPORT | 317 | 中文代码支持 |
| 17 | GIT COMMITS | 611 | Git 提交 |
| 18 | TOOL DISCIPLINE | 1381 | 不用 shell 做文件操作；bash 只用于 git/build/package |
| 19 | EXECUTION DISCIPLINE | 4389 | SKILL FIRST；FIX DON'T HIDE；EDIT WITH EDIT TOOL |
| 20 | USER COMMUNICATION | 559 | 用户通信和轮询 |
| 21 | SKILLS | 3297 | 技能系统 |

## 4. 工具集（28 个）

### 按类别

| 类别 | 工具 | 数量 |
|------|------|------|
| 执行 | bash, bash_start, bash_poll, bash_kill | 4 |
| 文件 | read_file, write_file, edit_file, search_replace, list_directory, open_file | 6 |
| 搜索 | glob, grep, ast_grep | 3 |
| 代码分析 | list_symbols, read_symbol, find_references, trace_callees, trace_callers, trace_chain, file_dependencies, blast_radius | 8 |
| 会话 | list_sessions, recall | 2 |
| 技能 | list_skills, use_skill | 2 |
| 其他 | describe_self, fetch_output, schedule_wakeup | 3 |

### 代码分析工具（atomcode 独有，claude-code 没有）

| 工具 | 参数 | 说明 |
|------|------|------|
| `ast_grep` | pattern, paths, lang | AST 模式结构化代码搜索 |
| `list_symbols` | file_path | 列出函数/类/结构体/方法等符号 |
| `read_symbol` | file_path, symbol | 读取单个符号的完整源码 |
| `find_references` | symbol, path | 查找符号的所有引用 |
| `trace_callees` | symbol, depth | 正向调用图 |
| `trace_callers` | symbol, depth | 反向调用图 |
| `trace_chain` | from, to | 两符号间最短调用链 |
| `file_dependencies` | file | 文件依赖关系 |
| `blast_radius` | file | 修改文件的影响范围 |

## 5. agent loop 协议

### OpenAI 格式

```
REQ-01: system + user(prompt) + user(system-reminders)
  → mock 返回 tool_calls: [read_file]
  → atomcode 执行 read_file

REQ-03: system + user + assistant(tool_calls) + tool(role=tool) + user(system-reminder)
  → mock 返回最终文本
  → atomcode 输出结果
```

### 与 Anthropic 格式对比

| 维度 | claude-code | atomcode |
|------|-------------|----------|
| tool_use | `content: [{type: "tool_use", id, name, input}]` | `tool_calls: [{id, function: {name, arguments}}]` |
| tool_result | `role: "user", content: [{type: "tool_result", ...}]` | `role: "tool", {tool_call_id, content}` |
| 参数 | `input` (object) | `arguments` (JSON string) |

## 6. 沙箱与安全

- **工作目录沙箱**：read_file 被限制在 cwd 内（`/etc/hostname` 被拒绝："outside the world's root"）
- **system-reminder 注入**：在 user 消息中注入探索前提醒 + 日期提醒
- **标题生成并行**：主请求与标题生成请求并行发出

## 7. 与 claude-code 全面对比

| 维度 | claude-code | atomcode |
|------|-------------|----------|
| 二进制 | 246MB Bun ELF (JSC bytecode) | 46MB C/C++ ELF (stripped) |
| API | Anthropic `/v1/messages` | OpenAI `/v1/chat/completions` |
| system prompt | 5770 字符, 11 段 | 36810 字符, 22 段 |
| 工具数 | 20（运行时）/ 44（静态） | 28 |
| 代码分析 | 无 | 8 个符号/调用图工具 |
| 子 agent | 有（Agent/ListAgents） | 无 |
| 网络 | 有（WebFetch/WebSearch） | 无 |
| 后台任务 | 无 | 有（bash_start/poll/kill） |
| 配置 | `~/.claude/` (JSON) | `~/.atomcode/` (TOML) |
| 定位 | 通用 AI agent | 代码理解 agent |

## 8. 产出清单

| 位置 | 文件 | 内容 |
|------|------|------|
| `artifacts/recon/atomcode/` | req-01.json, req-02.json | 首轮捕获（--no-tools） |
| | loop-req-01~03.json | 多轮 loop 捕获（含 tool_use/tool_result） |
| | system-prompt.md | 完整 system prompt |
| | tools.json | 28 个工具定义 |
| | request-params.json, request-headers.json | 请求参数和头 |
| `knowledge/recon/atomcode/` | concepts/harness_structure.md | harness 结构与请求协议 |
| | apis/tool_catalog.md | 工具目录 |
| | apis/agent_loop_protocol.md | agent loop 协议 |
| `tools/recon/` | mock-atomcode.mjs | 基础 mock 端点 |
| | mock-atomcode-loop.mjs | 多轮 loop 驱动 mock |