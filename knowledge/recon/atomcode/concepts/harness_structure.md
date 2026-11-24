---
type: Concept
title: atomcode 的 harness 物理结构与请求协议
description: atomcode 是 C/C++ 编译的原生 ELF（46MB stripped），用 OpenAI 兼容接口（/v1/chat/completions），通过 mock 端点抓取到完整 system prompt（28380 字符，22 段）+ 28 个工具定义。
tags: [task.reverse_engineering, topic.harness, topic.architecture]
status: stable
sources:
  - resource: artifacts/recon/atomcode/req-02.json
    role: evidence
  - resource: /home/zigaa/.local/bin/atomcode
    role: implementation
created_at: "2026-10-23T00:00:00Z"
updated_at: "2026-10-23T00:00:00Z"
platforms: [agnostic]
target_versions: ["atomcode@2026-10-23"]
---

# atomcode 的 harness 物理结构与请求协议

## 二进制本质

| 属性 | 值 |
|------|-----|
| 大小 | 46 MB |
| 格式 | ELF 64-bit LSB PIE executable |
| stripped | yes |
| 运行时 | C/C++ 原生编译（非 Bun/JS） |
| 配置 | `~/.atomcode/config.toml`（TOML） |
| API 接口 | OpenAI 兼容（`/v1/chat/completions`） |
| 默认 provider | AtomGit（`https://llm-api.atomgit.com/v1`） |

与 claude-code（246MB Bun 编译，JSC bytecode 内嵌）不同，atomcode 是纯原生 C/C++ 编译的 ELF，体积小（46MB），stripped。

## B 路线抓取方法

1. 在 `~/.atomcode/config.toml` 中定义 mock provider，base_url 指向 `http://127.0.0.1:3456/v1`
2. 用 `HOME=/tmp/atomcode-home` 重定向数据目录（绕过沙箱只读限制）
3. 单条命令内：起 mock server + 跑 `atomcode --config <mock-cfg> -p "hello" --dev --no-tools`
4. mock 落盘请求体到 `artifacts/recon/atomcode/`

## 请求协议

| 项 | 值 |
|----|-----|
| 端点 | `POST /v1/chat/completions` |
| 格式 | OpenAI 兼容 |
| stream | true（SSE） |
| max_tokens | 32768 |
| model | qwen3.8-27b |

### messages 结构

```
system (28380 chars) — 完整 system prompt
user (prompt) — 用户输入
user (system-reminder) — 日期等环境信息
```

## system prompt 结构（22 段）

| # | 段标题 | 字符数 | 内容 |
|---|--------|--------|------|
| 0 | 身份定义 | 719 | "You are AtomCode, an AI coding agent by AtomGit..." |
| 1 | PRECEDENCE | 659 | 优先级规则 |
| 2 | CONTENT SAFETY | 2299 | 内容安全 |
| 3 | SYSTEM REMINDERS | 595 | 系统提醒 |
| 4 | MCP SERVER INSTRUCTIONS | 687 | MCP 服务器指令 |
| 5 | CONTEXT MANAGEMENT | 410 | 上下文管理 |
| 6 | WORKFLOW | 2221 | 工作流 |
| 7 | TOOLS | 3222 | 工具说明 |
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
| 18 | TOOL DISCIPLINE | 1381 | 工具纪律（强制） |
| 19 | EXECUTION DISCIPLINE | 4389 | 执行纪律（强制） |
| 20 | USER COMMUNICATION AND POLLING | 559 | 用户通信和轮询 |
| 21 | SKILLS | 3297 | 技能 |

与 claude-code（11 段，5770 字符）对比：atomcode 的 system prompt 长 5 倍，段数翻倍，有明确的 WORKFLOW、DISCIPLINE、SKILLS 等段。

## 与 claude-code 对比

| 维度 | claude-code | atomcode |
|------|-------------|----------|
| 二进制 | 246MB Bun ELF (JSC bytecode) | 46MB C/C++ ELF (stripped) |
| API | Anthropic `/v1/messages` | OpenAI `/v1/chat/completions` |
| system prompt | 5770 字符, 11 段 | 28380 字符, 22 段 |
| 工具数 | 20（运行时）/ 44（静态契约） | 28 |
| 配置 | `~/.claude/` (JSON) | `~/.atomcode/` (TOML) |
| 会话恢复 | `--continue`/`--resume` | `--continue`/`--resume` |
| 子命令 | 无 | login/status/review/mcp/daemon/webui/plugin/hooks/schedule |