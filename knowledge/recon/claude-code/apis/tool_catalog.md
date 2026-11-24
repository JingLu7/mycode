---
type: API
title: claude-code 工具目录（非交互模式 20 工具）
description: claude-code@2.1.296 在非交互 -p 模式下暴露 20 个工具；sdk-tools.d.ts 声明 43 个，其余可能需特定 flag 或 plan mode 激活。
tags: [task.reverse_engineering, topic.tool_system, topic.harness]
status: stable
sources:
  - resource: artifacts/recon/tools.json
    role: primary
  - resource: /home/zigaa/.local/lib/node_modules/@anthropic-ai/claude-code/sdk-tools.d.ts
    role: constraint
created_at: "2026-10-12T00:00:00Z"
updated_at: "2026-10-12T00:00:00Z"
platforms: [agnostic]
target_versions: ["claude-code@2.1.296"]
---

# claude-code 工具目录

## 非交互模式（`-p`）捕获的 20 个工具

| 工具 | 类别 | 说明 |
|------|------|------|
| `Agent` | 子 agent | 启动子 agent 处理任务 |
| `Bash` | 执行 | 运行 bash 命令 |
| `Edit` | 文件 | 精确字符串替换编辑 |
| `Read` | 文件 | 读取文件/目录 |
| `Write` | 文件 | 写入文件 |
| `NotebookEdit` | 文件 | 编辑 Jupyter notebook |
| `WebFetch` | 网络 | 抓取 URL 内容 |
| `WebSearch` | 网络 | 网页搜索 |
| `Skill` | 元 | 加载 skill |
| `Workflow` | 元 | 工作流 |
| `CronCreate` | 调度 | 创建定时任务 |
| `CronDelete` | 调度 | 删除定时任务 |
| `CronList` | 调度 | 列出定时任务 |
| `EnterWorktree` | git | 进入 worktree |
| `ExitWorktree` | git | 退出 worktree |
| `ListAgents` | 子 agent | 列出可用 agent |
| `SendMessage` | 通信 | 发送消息 |
| `ReportFindings` | 通信 | 报告发现 |
| `ScheduleWakeup` | 调度 | 安排唤醒 |
| `TaskStop` | 控制 | 停止任务 |

## 与 sdk-tools.d.ts 的差异

`sdk-tools.d.ts`（171KB）声明 43 个工具契约。本次非交互模式只捕获到 20 个，其余可能需要：

- 交互式 TUI 模式
- `--plan` 或特定 flag
- 特定权限模式（如 `bypassPermissions`）
- 特定 session 状态

## 交叉验证

B 路线（动态抓取）拿到的 20 个工具 schema 与 D 路线（sdk-tools.d.ts 白盒契约）交叉验证：20 个工具的 `name` 和 `input_schema` 均能在 sdk-tools.d.ts 中找到对应类型定义。