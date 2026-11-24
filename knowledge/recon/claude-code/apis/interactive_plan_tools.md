---
name: interactive-plan-tools
description: 交互/计划工具（AskUserQuestion、PlanMode、Task*、ProposeGoal、ReportFindings 等）的契约与模式相关注册规则
type: concept
domain: recon
route: claude-code
profile: apis
source: artifacts/recon/tool-contracts.json
method: R1 白盒解析 d.ts + 运行时 -p 模式工具列表交叉验证
created: 2026-10-13
---

# 交互/计划工具契约

claude-code 的 44 个工具契约中，有一批用于用户交互、计划制定、任务管理和反馈报告。这些工具的注册取决于运行模式。

## 模式相关注册规则

`-p` 非交互模式只注册**不需要 UI 交互**的工具子集。运行时捕获 20 个工具中，交互/计划类工具的注册状态：

| 工具 | -p 模式 | 说明 |
|------|---------|------|
| AskUserQuestion | ❌ 不注册 | 需要用户选择 |
| EnterPlanMode | ❌ 不注册 | 需要用户确认计划 |
| ExitPlanMode | ❌ 不注册 | 需要用户批准执行 |
| TaskCreate / TaskGet / TaskUpdate / TaskList | ❌ 不注册 | Task 系统在 -p 模式不启用 |
| TaskStop | ✅ 注册 | 停止后台任务，不需 UI |
| ProposeGoal / ProposeSkills | ❌ 不注册 | 需要用户审批 |
| ReportFindings | ✅ 注册 | 报告审查结果，不需 UI |
| ScheduleWakeup | ✅ 注册 | 安排唤醒，不需 UI |
| EnterWorktree / ExitWorktree | ✅ 注册 | Git worktree 管理，不需 UI |
| PushNotification / ReadNotifications | ❌ 不注册 | 需要通知 UI |
| ShowOnboardingRolePicker / OfferChromeSetup | ❌ 不注册 | 需要 onboarding UI |
| ClaudeDesign / Monitor / RemoteTrigger / SendFeedback | ❌ 不注册 | 需要 UI |

**推断**：交互模式（非 -p）会注册全部 44 个工具（或接近全部），包括需要 UI 交互的工具。

## 核心工具契约

### AskUserQuestion

向用户提问，获取选择结果。

**输入**：
- `questions`: 数组（1-4 个问题）
  - `question`: string — 完整问题文本
  - `header`: string — 短标签（max 12 chars），如 "Auth method"
  - `options`: 数组（2-4 个选项）
    - `label`: string — 显示文本（1-5 words）
    - `description`: string — 选项解释
    - `preview`: string (可选) — 聚焦时渲染的预览内容
  - `multiSelect`: boolean — 是否允许多选

**输出**（由权限组件收集）：
- `answers`: { [question: string]: string } — 用户选择
- `annotations`: { [question: string]: { preview?: string } } — 附注
- `notes`: string — 自由文本备注
- `metadata`: { source?: string } — 分析追踪

### EnterPlanMode / ExitPlanMode

计划模式控制。

**EnterPlanMode**：无参数。进入计划模式（只读，不执行修改）。

**ExitPlanMode**：
- `prompt`: string (required) — 语义描述，如 "run tests"、"install dependencies"
- `allowedPrompts`: deprecated，不再使用

退出计划模式时请求用户批准执行某些操作。

### Task 系列

后台任务管理（-p 模式仅注册 TaskStop）。

**TaskCreate**：
- `subject`: string (required) — 任务标题
- `description`: string (required) — 任务描述
- `activeForm`: string — 进行中显示文本（如 "Running tests"）
- `metadata`: object — 任意元数据

**TaskGet**：
- `taskId`: string (required)

**TaskUpdate**：
- `taskId`: string (required)
- `subject` / `description` / `activeForm`: 可选更新
- `status`: "pending" | "in_progress" | "completed" | "deleted"
- `addBlocks`: string[] — 此任务阻塞的任务 ID
- `addBlockedBy`: string[] — 阻塞此任务的任务 ID
- `owner`: string
- `metadata`: object — 合并元数据（null 值删除键）

**TaskList**：无参数。

**TaskStop**：
- `task_id`: string — 后台任务 ID（也接受 agent-team 队友和命名后台 agent 的 ID 或名称）
- `shell_id`: string (deprecated)

### ProposeGoal

提出完成条件，由独立评估器验证。

- `condition`: string (required) — 完成条件，如 "all tests in test/auth pass"
- `ask_user`: boolean — 是否请求用户审批（默认 true）

### ReportFindings

报告代码审查发现。

- `findings`: 数组 (required) — 验证后的发现，最严重在前
  - `file`: string — 仓库相对路径
  - `line`: number — 1-indexed 行号
  - `summary`: string — 一句话描述
  - `short_summary`: string — 紧凑标签（≤60 chars）
  - `failure_scenario`: string — 具体输入/状态 → 错误输出/崩溃
  - `category`: string — kebab-case，如 "correctness"、"simplification"
  - `verdict`: "CONFIRMED" | "PLAUSIBLE"
  - `outcome`: "fixed" | "skipped" | "no_change_needed"
- `summary`: string (required)
- `failure_scenario`: string (required)
- `level`: "low" | "medium" | "high" | "xhigh" | "max"

## 解析限制

R1 的 `dump_tool_contracts.py` 对内联对象类型和索引签名 `[k: string]: unknown` 解析不够精确，会将索引签名误拆为单独属性。例如 ExitPlanMode 的 `allowedPrompts` 类型为 `{ tool: "Bash"; prompt: string; [k: string]: unknown }`，解析后 `k` 被误列为 required 字段。使用时需人工修正此类字段。