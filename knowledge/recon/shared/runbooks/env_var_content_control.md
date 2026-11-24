---
type: Runbook
title: CLAUDE_CODE_SIMPLE 等环境变量控制请求内容量
description: claude-code 在 CLAUDE_CODE_SIMPLE=1 时精简 system prompt 和工具列表；逆向完整内容时必须关掉此变量。
tags: [task.reverse_engineering, topic.system_prompt, topic.tool_system]
status: stable
sources: []
created_at: "2026-10-12T00:00:00Z"
updated_at: "2026-10-12T00:00:00Z"
platforms: [agnostic]
---

# 环境变量控制内容量

## 症状

用 mock 端点抓取 claude-code 请求，system prompt 只有约 500 字符，工具列表不完整。与预期（完整 system prompt ~5800 字符、20 个工具）差距很大。

## 根因

`CLAUDE_CODE_SIMPLE=1` 环境变量触发精简模式，裁剪 system prompt 分段和工具 schema。其他可能影响内容的环境变量包括 `CLAUDE_CODE_SKIP_QUEUES` 等。

## 处置

逆向完整内容时**不要设置** `CLAUDE_CODE_SIMPLE`：

```bash
unset CLAUDE_CODE_SIMPLE
ANTHROPIC_BASE_URL=http://127.0.0.1:3456 claude -p "hello"
```

如需排查哪些环境变量影响内容，用 `strings` 提取 `CLAUDE_CODE_*` 前缀的字符串常量。

## 验证

- system prompt 长度 > 5000 字符，包含 `# Harness`、`# Memory`、`# Context management` 等分段标题。
- tools 数组长度 >= 15。