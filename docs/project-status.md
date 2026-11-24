# mycode 项目状态

> 最后更新：2026-10-23
> 工作目录：`/data/taoming/project/mycode`

## 一、项目目标

逆向 Claude Code（`@anthropic-ai/claude-code@2.1.296`）的 agent 工作流与 harness，作为设计参照，用 Python 实现对齐的本地 AI 编程助手 **mycode**。模型层调用宿主 ollama（:11434）的本地模型。

## 二、逆向 claude-code 产出（B 路线已完成）

### 方法论

A+B+D 组合（静态字符串 + 动态抓取 + 白盒契约），详见 `knowledge/recon/shared/concepts/reverse_engineering_routes.md`。

### 产出（`artifacts/recon/`）

| 文件 | 内容 |
|------|------|
| `capture-full-mode.json` | claude 真实完整 API 请求（68KB，含 system+tools） |
| `system-prompt.md` | 完整 system prompt（5770 字符，11 段） |
| `tools.json` | 20 个工具的完整 JSON schema（53KB） |
| `tool-contracts.json` | 工具契约 |
| `request-skeleton.json` | 请求顶层参数骨架 |
| `request-headers.json` | 完整请求头（含 anthropic-beta 特性列表） |
| `env-vars.txt` | 环境变量 |
| `r3/` | 逆向抓取的请求体证据（error/parallel 各 2 个） |

### 关键发现

- **请求参数**：`model=claude-opus-5-5`、`max_tokens=128000`、`thinking={adaptive,display:omitted}`、`output_config={effort:medium}`
- **Beta 头**：`interleaved-thinking`、`context-management`、`prompt-caching-scope`、`effort`、`dangerous-tool-use` 等
- **system prompt 分段**：billing → agent 身份 → 安全策略 → Harness → 代码风格 → Memory → Environment → Context management
- **工具集**：20 个工具（运行时）/ 44 个（静态契约）

## 三、逆向 atomcode 产出（2026-10-23 启动，B 路线首轮已完成）

### 产出（`artifacts/recon/atomcode/`）

| 文件 | 内容 |
|------|------|
| `req-01.json` | 标题生成请求（system prompt 218 字符，无工具） |
| `req-02.json` | 主请求（system prompt 28380 字符，28 工具） |
| `system-prompt.md` | 完整 system prompt（28380 字符，22 段） |
| `tools.json` | 28 个工具定义 |
| `request-params.json` | 请求参数 |
| `request-headers.json` | 请求头 |

### 关键发现

- **二进制**：C/C++ 编译的原生 ELF（46MB stripped），非 Bun/JS
- **API**：OpenAI 兼容接口（`/v1/chat/completions`），非 Anthropic 格式
- **system prompt**：28380 字符，22 段（比 claude-code 长 5 倍）
- **工具集**：28 个工具，含 AST 搜索/符号分析/调用图/依赖管理等代码理解工具
- **配置**：`~/.atomcode/config.toml`（TOML），provider 可重定向

### 与 claude-code 对比

| 维度 | claude-code | atomcode |
|------|-------------|----------|
| 二进制 | 246MB Bun ELF (JSC bytecode) | 46MB C/C++ ELF (stripped) |
| API | Anthropic `/v1/messages` | OpenAI `/v1/chat/completions` |
| system prompt | 5770 字符, 11 段 | 28380 字符, 22 段 |
| 工具数 | 20（运行时）/ 44（静态） | 28 |
| 定位 | 通用 AI agent（子 agent/网络/工作流） | 代码理解 agent（符号/调用图/依赖） |

## 四、mycode 开发状态

### 分层架构（`src/mycode/`）

```
agent/    — agent loop + context + transcript + context_management
cli/      — CLI 入口（单轮 + --continue/--resume + REPL）
harness/  — hooks + permissions + memory + subagent + skills + settings + plugins
llm/      — Ollama 适配器（num_ctx/thinking/tool_calling）
prompt/   — system prompt 生成（8 段含 Memory）
tools/    — 20 个工具文件 + contract_tools.py（24 契约工具）
```

### 开发阶段

| 阶段 | 状态 | 内容 |
|------|------|------|
| P0 地基 | ✅ | agent loop + Bash/Read/Write + ollama 适配器 + CLI |
| P1 harness 核心 | ✅ | 6 工具 + 权限管理 + system prompt 增强 + transcript + context management |
| P2 扩展 | ✅ | 22 工具 + Subagent + Hooks + Skill + Cron/Workflow/Worktree/Messaging |
| 全量对齐 | ✅ | 44 工具 + harness（hooks/权限/memory/上下文/skill/plugins）+ prompt 全量对齐 |
| 多轮会话 | ✅ | transcript 持久化 + --continue/--resume + REPL 交互模式 |

### 工具对齐

24 个契约工具（`contract_tools.py`）+ builtin 工具 = **44 工具全量对齐** sdk-tools.d.ts

## 五、评测基准（2026-10-13）

### 方法

inference/eval 解耦（借鉴 SWE-bench），同一试卷跑 mycode vs claude-code，统一评分器（非 LLM-as-judge）。

### 结果

| 指标 | mycode | claude-code |
|------|--------|-------------|
| 通过率 | **11/12 (91.7%)** | **11/12 (91.7%)** |
| 平均耗时 | **11.2s** | 60.2s |

mycode 快 5.4 倍，失败题不同（互为补充）。

## 六、知识沉淀（OKF v0.2）

`knowledge/recon/` 下知识卡：

| route | 数量 | 内容 |
|-------|------|------|
| claude-code/concepts | 3 | system_prompt 结构、harness 结构、agent_loop 协议 |
| claude-code/apis | 7 | runtime 机制、交互计划工具、agent loop、工具契约解析、beta 头、工具目录、请求参数 |
| atomcode/concepts | 1 | harness 结构与请求协议 |
| atomcode/apis | 1 | 工具目录（28 个工具） |
| shared/concepts | 1 | 逆向工程路线方法论 |
| shared/runbooks | 5 | 环境变量控制、ollama thinking/tool_call、沙箱进程清理、mock 端点抓取、SSE 流式要求 |
| codex | 预留 | 待启动 |

## 七、下一步计划

| 项 | 状态 | 说明 |
|----|------|------|
| 逆向 atomcode 深入 | 🔲 进行中 | B 路线首轮完成，待深入：多轮 loop 抓取、工具 schema 解析、system prompt 逐段分析 |
| 逆向 codex | 🔲 待启动 | 知识体系已预留 |
| P3 方向 | ⏸️ 后移 | context_management 细化、subagent 并行、hooks 配置加载 |