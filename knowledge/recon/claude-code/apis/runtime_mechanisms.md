---
name: runtime-mechanisms
description: claude-code 运行时机制：hooks（9 种事件）、permission（模式+规则）、memory（CLAUDE.md+auto-memory）、context management（压缩+clear_thinking）、skills、settings 层级
type: concept
domain: recon
route: claude-code
profile: apis
source: claude --help + system-prompt.md + claude.exe grep + ~/.claude/ 目录结构
method: help 输出 + system prompt 分析 + 二进制字符串搜索 + 配置目录结构
created: 2026-10-13
---

# 运行时机制

claude-code 的 harness 围绕 agent loop 构建了多层运行时机制。以下为各机制的逆向结果。

## Hooks

### 事件类型（9 种）

| 事件 | 触发时机 | 二进制出现次数 |
|------|---------|--------------|
| PreToolUse | 工具调用前 | 125 |
| PostToolUse | 工具调用后 | 94 |
| Notification | 通知发送时 | 253 |
| Stop | agent 停止时 | 570 |
| SubagentStop | 子 agent 停止时 | 37 |
| PreCompact | 上下文压缩前 | 28 |
| SessionStart | 会话开始时 | 105 |
| SessionEnd | 会话结束时 | 39 |
| UserPromptSubmit | 用户提交 prompt 时 | 51 |

### 配置方式

- 在 `settings.json` 的 `hooks` 字段中定义
- 使用 `matcher` 匹配工具名（如 `matcher: "Bash"`）
- 插件也可定义 hooks（`--bare` 跳过 settings 和插件 hooks）
- `--debug "hooks"` 可调试 hooks 执行

### 控制开关

| flag | 行为 |
|------|------|
| `--bare` | 跳过 hooks（settings + 插件定义的） |
| `--safe-mode` | 禁用 hooks 及所有自定义 |
| `-d "hooks"` | 启用 hooks 调试日志 |

### system prompt 中的描述

> Hooks may intercept tool calls; treat hook output as user feedback.

hook 输出被视为用户反馈，注入到对话中。

## Permission

### 权限模式

| 模式 | 说明 |
|------|------|
| `default` | 默认模式，每次危险操作询问用户 |
| `acceptEdits` | 自动接受文件编辑 |
| `plan` | 计划模式，只读不执行修改 |
| `bypassPermissions` | 跳过所有权限检查 |

### 配置方式

- `safeguards.classifier_context.permission_mode` 在请求参数中传递
- `allowRules` / `denyRules` — 允许/拒绝规则
- `allowedTools` / `--allowed-tools` — 允许的工具列表
- permission handler 可配置（`--restricted` 模式下由 handler 审批）

### 控制开关

| flag | 行为 |
|------|------|
| `--dangerously-skip-permissions` | 跳过所有权限检查 |
| `--allow-dangerously-skip-permissions` | 启用跳过权限选项 |
| `--restricted` | 受限模式，移除命令执行工具，拒绝 bypassPermissions |

### system prompt 中的描述

> Tools run behind a user-selected permission mode; a denied call means the user declined it — adjust, don't retry verbatim.

## Memory

### 层级结构

| 层级 | 路径 | 说明 |
|------|------|------|
| 全局 | `~/.claude/CLAUDE.md` | 全局行为指南 |
| 项目级 | `<project>/CLAUDE.md` 或 `<project>/AGENTS.md` | 项目级指令 |
| auto-memory | `~/.claude/projects/<encoded-path>/memory/` | 自动记忆目录 |

路径编码：`/data/taoming/mycode` → `-data-taoming-mycode`

### 记忆格式

每个记忆是一个 `.md` 文件，含 frontmatter：

```markdown
---
name: <short-kebab-case-slug>
description: <one-line summary>
metadata:
  type: user | feedback | project | reference
---
<body>
```

- `user`: 用户角色、专长、偏好
- `feedback`: 用户给予的工作指导（含 why）
- `project`: 进行中的工作、目标、约束
- `reference`: 外部资源指针

### MEMORY.md 索引

- 每行一条记忆指针：`- [Title](file.md) — hook`
- 每个会话加载到上下文
- 不放记忆正文，只放索引

### 控制开关

| flag | 行为 |
|------|------|
| `--bare` | 跳过 auto-memory 和 CLAUDE.md auto-discovery |
| `--safe-mode` | 禁用 CLAUDE.md |

### system prompt 中的描述

> You have a persistent file-based memory at `<path>`. This directory already exists — write to it directly with the Write tool.

## Context Management

### 请求参数

```json
{
  "context_management": {
    "type": "clear_thinking_20251015",
    "keep": "all"
  }
}
```

- `clear_thinking_20251015`: 清除 thinking token
- `keep: "all"`: 保留所有消息

### beta header

`context-management-2025-06-27` 启用上下文管理特性。

### 自动压缩

- `--autocompact <auto|tokens>`: 自动压缩窗口大小
- 长对话时自动摘要，摘要 + 未摘要内容放入下一个上下文窗口
- `PreCompact` hook 在压缩前触发

### 轮次标记

每轮追加 system message：`<total_tokens>14999980 tokens left</total_tokens>`

### system prompt 中的描述

> When the conversation grows long, some or all of the current context is summarized; the summary, along with any remaining unsummarized context, is provided in the next context window so work can continue.

## Skills

### 目录结构

```
~/.claude/skills/<skill-name>/
  SKILL.md          # 入口文件（frontmatter + 正文）
  agents/           # 角色 prompt
  assets/           # 静态资源
  references/       # 参考文档
  scripts/          # 脚本
```

### SKILL.md frontmatter

```yaml
---
name: <skill-name>
description: <触发条件描述>
---
```

### 触发方式

- 用户输入 `/<skill-name>` 命令
- 描述匹配自动触发

### 控制开关

| flag | 行为 |
|------|------|
| `--disable-slash-commands` | 禁用所有 skills |
| `--safe-mode` | 禁用 skills |
| `--bare` | skills 仍可通过 /skill-name 解析 |

## Settings 层级

| 层级 | 路径 | 说明 |
|------|------|------|
| user | `~/.claude/settings.json` | 全局配置 |
| project | `<project>/.claude/settings.json` | 项目级配置 |
| local | `<project>/.claude/settings.local.json` | 本地配置 |
| managed | 系统级 | 管理员配置 |

### settings.json 主要字段

```json
{
  "env": { /* 环境变量覆盖 */ },
  "model": "模型ID",
  "enabledPlugins": { /* 插件启用/禁用 */ },
  "hooks": { /* hooks 配置 */ },
  "skipDangerousModePermissionPrompt": true,
  "theme": "dark"
}
```

### 控制开关

| flag | 行为 |
|------|------|
| `--settings <file>` | 加载额外 settings |
| `--setting-sources <sources>` | 指定来源（user,project,local） |
| `--restricted` | 忽略 user/project/local settings |
| `--safe-mode` | 禁用所有自定义（保留 managed settings） |

## Plugins

### 目录结构

```
~/.claude/plugins/
  installed_plugins.json    # 已安装插件清单
  known_marketplaces.json   # 已知市场
  cache/                    # 插件缓存
  marketplaces/             # 市场数据
```

### installed_plugins.json

每条记录含：scope、installPath、version、installedAt、gitCommitSha。

### settings.json 控制

`enabledPlugins` 字段控制每个插件的启用/禁用。