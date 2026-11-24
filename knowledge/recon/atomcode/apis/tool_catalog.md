---
type: API
title: atomcode 的 28 个工具定义
description: 通过 mock 端点抓取到的 atomcode 运行时工具集（28 个），含 AST 搜索、符号分析、调用图追踪等代码理解工具，与 claude-code 工具集有显著差异。
tags: [task.reverse_engineering, topic.tools, topic.api]
status: stable
sources:
  - resource: artifacts/recon/atomcode/tools.json
    role: evidence
created_at: "2026-10-23T00:00:00Z"
updated_at: "2026-10-23T00:00:00Z"
platforms: [agnostic]
target_versions: ["atomcode@2026-10-23"]
---

# atomcode 的 28 个工具定义

## 工具清单

| 工具 | 说明 | 类别 |
|------|------|------|
| `bash` | 在工作目录运行 shell 命令 | 执行 |
| `bash_start` | 后台启动 shell 命令，返回 job id | 执行 |
| `bash_poll` | 读取后台 bash 任务的输出 | 执行 |
| `bash_kill` | 停止后台 bash 任务 | 执行 |
| `read_file` | 读取文件（或文件切片） | 文件 |
| `write_file` | 写文件 | 文件 |
| `edit_file` | 替换文件中的精确文本片段 | 文件 |
| `search_replace` | 跨多文件查找替换 | 文件 |
| `glob` | glob 模式查找文件 | 搜索 |
| `grep` | 正则搜索文件内容 | 搜索 |
| `ast_grep` | AST 模式结构化代码搜索 | 代码分析 |
| `list_directory` | 列目录树 | 文件 |
| `list_symbols` | 列出函数/类/结构体/方法等符号 | 代码分析 |
| `read_symbol` | 读取单个符号的完整源码 | 代码分析 |
| `find_references` | 查找符号的所有引用 | 代码分析 |
| `trace_callees` | 追踪符号的所有被调用者（正向调用图） | 代码分析 |
| `trace_callers` | 追踪符号的所有调用者（反向调用图） | 代码分析 |
| `trace_chain` | 查找两个符号间最短调用链 | 代码分析 |
| `file_dependencies` | 显示文件的依赖关系 | 代码分析 |
| `blast_radius` | 估算修改文件的影响范围 | 代码分析 |
| `list_sessions` | 列出项目的历史会话 | 会话 |
| `recall` | 读取项目已完成的历史对话轮次 | 会话 |
| `list_skills` | 搜索可用技能 | 技能 |
| `use_skill` | 调用命名技能 | 技能 |
| `schedule_wakeup` | 安排定时唤醒 | 调度 |
| `open_file` | 在 GUI 中打开文件/目录/URL | 交互 |
| `describe_self` | 报告 agent 的组装方式 | 元信息 |
| `fetch_output` | 读取被截断的大输出 | 辅助 |

## 与 claude-code 工具集对比

### 共有工具（功能等价）

| atomcode | claude-code | 说明 |
|----------|-------------|------|
| `bash` | `Bash` | shell 命令执行 |
| `read_file` | `Read` | 读文件 |
| `write_file` | `Write` | 写文件 |
| `edit_file` | `Edit` | 编辑文件 |
| `glob` | `Glob` | glob 查找 |
| `grep` | `Grep` | 正则搜索 |

### atomcode 独有（代码分析向）

`ast_grep`、`list_symbols`、`read_symbol`、`find_references`、`trace_callees`、`trace_callers`、`trace_chain`、`file_dependencies`、`blast_radius` — 这些工具使 atomcode 具备**符号级代码理解**能力（调用图、引用查找、影响分析），是 claude-code 没有的。

### atomcode 独有（执行管理）

`bash_start`/`bash_poll`/`bash_kill`（后台任务管理）、`fetch_output`（截断输出读取）、`schedule_wakeup`（定时唤醒） — 更细粒度的执行控制。

### atomcode 独有（会话/技能）

`list_sessions`、`recall`、`list_skills`、`use_skill`、`describe_self`、`open_file`、`search_replace` — 会话回溯、技能系统、多文件替换。

### claude-code 独有（atomcode 没有）

`Agent`（子 agent）、`WebFetch`/`WebSearch`（网络）、`NotebookEdit`、`Cron*`、`Workflow`、`Worktree`、`Skill`、`TodoWrite`、`TaskStop`、`ListAgents`、`SendMessage`/`ReportFindings` — claude-code 有子 agent 和网络能力，atomcode 没有。

## 定位差异

- **claude-code**：通用 AI agent，强调子 agent 并行、网络访问、工作流编排
- **atomcode**：代码理解向 agent，强调符号分析、调用图、依赖管理、后台执行