---
type: Runbook
title: 沙箱清理跨命令后台进程，须同命令内起 server 与跑 CLI
description: 在沙箱环境中，上一条 bash 命令启动的后台进程（如 mock server）会被下一条命令执行前清理；必须在同一条 bash 命令内启动 server 并运行 agent CLI。
tags: [task.reverse_engineering, topic.sandbox, topic.mock_capture]
status: stable
sources: []
created_at: "2026-10-12T00:00:00Z"
updated_at: "2026-10-12T00:00:00Z"
platforms: [agnostic]
---

# 沙箱进程清理

## 症状

在 bash 工具中分两步操作：
1. 启动 mock server：`node mock.mjs &`（后台运行）
2. 运行 agent CLI：`ANTHROPIC_BASE_URL=... claude -p "hello"`

第二步执行时，mock server 已经不存在，agent CLI 报连接拒绝（ECONNREFUSED）。

## 根因

沙箱环境在每条 bash 命令执行前清理上一条命令留下的后台进程。`&` 启动的 server 生命周期只限于当前命令。

## 处置

把启动 server 和运行 CLI 放在**同一条 bash 命令**内：

```bash
node mock.mjs & SERVER_PID=$!; sleep 0.3; ANTHROPIC_BASE_URL=http://127.0.0.1:3456 claude -p "hello"; kill $SERVER_PID
```

或者用 `&&` 串联，确保 server 在 CLI 运行期间存活。

## 验证

- agent CLI 成功连接 mock server，请求体落盘。
- 落盘文件非空且包含合法 JSON。