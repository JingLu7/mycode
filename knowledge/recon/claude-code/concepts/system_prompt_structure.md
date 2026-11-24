---
type: Concept
title: claude-code system prompt 分段结构
description: 完整 system prompt 约 5770 字符，分 11 段：billing header、agent 身份、安全策略、Harness、代码风格、代词、不可逆操作、Session guidance、Memory、Environment、Context management。
tags: [task.reverse_engineering, topic.system_prompt, topic.harness]
status: stable
sources:
  - resource: artifacts/recon/system-prompt.md
    role: primary
created_at: "2026-10-12T00:00:00Z"
updated_at: "2026-10-12T00:00:00Z"
platforms: [agnostic]
target_versions: ["claude-code@2.1.296"]
---

# claude-code system prompt 分段结构

完整 system prompt 约 5770 字符，分 11 段。通过 mock 端点抓取（`CLAUDE_CODE_SIMPLE` 未设置时）。

## 分段清单

| 序号 | 标题/特征 | 内容摘要 |
|------|----------|---------|
| 1 | billing header | API credit 信息 |
| 2 | agent 身份 | "You are Claude Code, Anthropic's official CLI..." |
| 3 | 安全策略 | 危险操作确认、路径限制 |
| 4 | `# Harness` | 权限模式、系统消息处理、hooks 当用户反馈、文件工具优先、并行、代码引用 |
| 5 | 代码风格 | 简洁、surgical changes、match existing style |
| 6 | 代词 | they/them |
| 7 | 不可逆操作 | git push --force、rm 等需确认 |
| 8 | `# Session-specific guidance` | skills 加载 |
| 9 | `# Memory` | 文件记忆 + MEMORY.md 索引（与 auto-memory 同构） |
| 10 | `# Environment` | 工作目录、平台、git 状态 |
| 11 | `# Context management` | 自动摘要、token 预算 |

## 关键设计

- **`# Harness` 段**：定义 agent 的操作约束——权限模式（default/acceptEdits/plan/bypassPermissions）、系统消息作为用户反馈、文件工具优先于 bash、并行工具调用、代码引用格式。
- **`# Memory` 段**：定义文件记忆系统——`MEMORY.md` 索引 + 分类记忆文件，与 Claude Code 的 auto-memory 功能同构。
- **`# Context management` 段**：定义自动摘要机制——token 接近上限时自动摘要旧对话。