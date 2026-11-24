---
name: p2-tool-completion-strategy
description: P2 阶段完善 22 个工具的策略和关键设计决策
type: concept
created: 2026-10-12
tags: [mycode, p2, tools, architecture]
---

# P2 工具完善策略

## 背景
claude-code 逆向捕获到 20 个工具（非交互模式），P0 实现了 3 个（Bash/Read/Write），P1 增加了 3 个（Edit/Glob/Grep）。P2 目标是完善所有工具 + subagent + hooks + skill。

## 关键设计决策

### 1. WebFetch 简化：不用小模型
claude-code 的 WebFetch 用"小模型"对页面内容跑 prompt，避免主上下文膨胀。
mycode 简化为：抓取 URL → HTML 转文本 → 截断返回（保留 offset 分页）。
主 agent 自己处理 prompt，无需额外模型调用，更透明。

### 2. WebSearch 用 DuckDuckGo HTML 端点
无需 API key，解析 HTML 结果页。支持 allowed_domains/blocked_domains 过滤。
DDG 的 href 是 redirect 链接，需从 `uddg=` 参数提取真实 URL。

### 3. Subagent 用独立 AgentLoop 实例
SubagentManager 是进程内单例，由 CLI 在启动时 configure(llm, tools, system_prompt)。
spawn 时创建新 AgentLoop（独立上下文），共享 LLM provider。
内置 3 种 agent 类型：general（全工具）、explore（只读）、coder（文件+bash）。

### 4. Hooks 集成到 AgentLoop
HookType: PreToolUse / PostToolUse / Stop / SubagentStop。
PreToolUse 可阻止或修改工具参数（返回 PreToolResult）。
PostToolUse 可修改工具结果。
AgentLoop 在工具执行前后和循环结束时调用 hooks。

### 5. Skill 用 YAML frontmatter markdown
Skill 文件放在 ~/.mycode/skills/*.md，简易 YAML 解析（不依赖 yaml 库）。
subagent=true 的 skill 在 subagent 中运行，否则返回内容作为指令注入对话。

### 6. 工具错误处理统一为返回字符串
所有工具 execute 函数返回 str，不抛异常。
预期错误（文件不存在、cell 不存在等）返回 "Error: ..." 字符串。
ToolRegistry.execute 兜底捕获未预期异常。

## 最终工具清单（22 个）
Bash, Read, Write, Edit, Glob, Grep, WebFetch, WebSearch, NotebookEdit, TaskStop,
Agent, ListAgents, Skill, CronCreate, CronDelete, CronList, EnterWorktree, ExitWorktree,
SendMessage, ReportFindings, ScheduleWakeup, Workflow