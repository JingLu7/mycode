# mycode 项目记忆（Project Memory）

> 由主 agent（项目管理角色）维护的项目上下文，供跨会话与零记忆 agent 复用。
> 最后更新：2026-10-12

## 一、任务目标
- 工作目录：`/data/taoming/project/mycode`，在此开发 **mycode 智能编程助手**。
- 核心方法：**逆向 Claude Code（`@anthropic-ai/claude-code@2.1.296`）的 agent 工作流（workflow）与 harness**，作为设计参照。
- 模型层：调用宿主 **ollama（:11434）** 的本地模型做测试。
- 用户已确认策略：**逆向路线先验证 B（动态抓取）可行性**；**开发并行推进**（边逆向边搭原型）。

## 二、环境事实（已实测）
- 宿主：`zigaa@zigaa-Precision-5820-Tower`（4090D，SSH 远程）。
- claude-code 全局安装：`/home/zigaa/.local/lib/node_modules/@anthropic-ai/claude-code`；命令 `/home/zigaa/.local/bin/claude`。
- 沙箱与宿主网络隔离：访问宿主 ollama 须用 `docker run --network host` 容器；**实测可达**。
- ollama **0.34.3**；模型：`qwen3-32b:latest`（19.8GB）、`deepseek-r1-32b:latest`（19.9GB）。
- 本机工具链：`bun` @ `/home/zigaa/.bun/bin/bun`；`node` v26.1.0；沙箱 `python3` + miniconda3。

## 三、逆向目标事实（已实测）
- 2.1.296 是 **Bun 编译的原生 ELF 单文件**：`bin/claude.exe`，246MB，`not stripped`（仅动态符号表 ~1230 项）。
- 含 `.bun_builtins` 段 → Bun standalone 产物；应用 JS 以 **JSC bytecode 内嵌**（非明文源码），**字符串常量明文**。
- 白盒资产：`sdk-tools.d.ts`（171KB）暴露 43 个工具契约。

## 四、逆向产出（已落盘 `artifacts/recon/`）
| 文件 | 内容 |
|---|---|
| `capture-full-mode.json` | claude 真实发出的完整 API 请求（68KB，含 system+tools） |
| `system-prompt.md` | 完整 system prompt（5770 字符） |
| `tools.json` | 20 个工具的完整 JSON schema（53KB） |
| `request-skeleton.json` | 请求顶层参数骨架 |
| `request-headers.json` | 完整请求头（含 anthropic-beta 特性列表） |
| `tools/recon/mock-anthropic.mjs` | 记录型 mock 端点（B 路线抓取工具） |

## 五、逆向发现：claude harness 关键设计（从捕获提炼）
- **请求参数**：`model=claude-opus-5-5`、`max_tokens=128000`、`thinking={adaptive,display:omitted}`、`context_management={clear_thinking_20251015}`、`output_config={effort:medium}`、`safeguards={dangerous_tool_use 分类器}`。
- **架构 Beta 头**：`claude-code-20250219`、`interleaved-thinking`、`context-management`、`prompt-caching-scope`、`mid-conversation-system`、`per-turn-control`、`effort`、`dangerous-tool-use`、`afk-mode` 等。
- **system prompt 分段结构**：billing header → agent 身份 → 安全策略 → `# Harness`（权限/系统消息/hooks/文件工具优先/并行/代码引用）→ 代码风格 → 不可逆操作确认 → `# Session-specific guidance` → `# Memory`（文件记忆 + `MEMORY.md` 索引，与本机 auto-memory 同构）→ `# Environment` → `# Context management`（自动摘要）→ `total_tokens`。
- **工具集（本次捕获 20 个）**：Agent、Bash、Edit、Read、Write、NotebookEdit、WebFetch、WebSearch、Skill、Workflow、Cron*、Enter/ExitWorktree、ListAgents、SendMessage、ReportFindings、ScheduleWakeup、TaskStop。

## 六、mycode 设计蓝图与实现状态
- **语言/形态**：Python CLI，LLM 走 ollama `/api/chat`。
- **分层**：`src/mycode/{agent,llm,tools,harness,prompt,cli}/`
- **分阶段**：P0 地基 → P1 harness 核心 → P2 扩展。
- **P0 已完成** ✅：agent loop + Bash/Read/Write + ollama 适配器 + CLI。
- **P1 已完成** ✅：6 工具（+Edit/Glob/Grep）+ 权限管理（default/auto）+ system prompt 增强（8 段含 Memory）+ 会话 transcript + context management（token 超限自动摘要）。测试通过。
- **P2 已完成** ✅：22 工具 + Subagent 系统（Agent/ListAgents + SubagentManager）+ Hooks 机制（PreToolUse/PostToolUse/Stop/SubagentStop）+ Skill 系统（YAML frontmatter）+ Cron/Workflow/Worktree/Messaging。全量集成测试和端到端测试通过。
- **harness 逆向报告已产出** ✅：`docs/harness-reverse-engineering-report.md`（8 章）。

## 七、知识沉淀体系（OKF v0.2）
- 仿照 `tools/cannbot-knowledge` 架构，在 `mycode/knowledge/` 下建立 OKF 知识库。
- **domain**：`recon`（逆向工程，按目标分 route：claude-code/codex/atomcode/shared）、`dev`（mycode 开发）。
- **路径 Profile**：concepts/apis/runbooks/guides/glossaries。
- **已沉淀 13 张知识卡**：5 张通用踩坑 + 6 张 claude-code 逆向发现 + 1 张方法论 + 1 张架构决策。
- **codex/atomcode 预留**：`knowledge/recon/codex/`、`knowledge/recon/atomcode/` 已建 index.md。
- 治理文件在 `governance/`（schemas + specs），变更日志在 `logs/`，工作约定在 `AGENTS.md`。

## 八、待决策（需用户拍板）
1. 真机端到端测试：需用户在宿主机跑 `PYTHONPATH=src python -m mycode "prompt"` 验证 ollama 连通。
2. P3 方向：更深入的 harness 还原（如 context_management 策略细化、subagent 并行执行、hooks 配置文件加载）。
3. 逆向 codex / atomcode：知识体系已预留位置，待用户启动。

## 更新日志
- 2026-10-12 初建：任务目标、环境与逆向目标探索。
- 2026-10-12 **B 路线验证成功**：mock 端点抓取 claude 真实请求（system+tools+headers），产出落盘。
- 2026-10-12 **mycode 地基验证成功**：ollama qwen3-32b tool-calling 可用（`think:false`）。
- 2026-10-12 **agent loop 协议逆向**：SSE 流式 mock 驱动完整循环，拿到 5 条 messages 结构。
- 2026-10-12 **知识沉淀体系初始化**：仿照 cannbot-knowledge 创建 OKF v0.2 知识库，沉淀 13 张知识卡。
- 2026-10-12 **harness 逆向报告产出**：`docs/harness-reverse-engineering-report.md`（8 章）。
- 2026-10-12 **P0 开发完成**：Python CLI + agent loop + 3 工具 + ollama 适配器，测试通过。
- 2026-10-12 **P1 开发完成**：6 工具 + 权限管理 + system prompt 增强 + transcript + context management，测试通过。
- 2026-10-12 **P2 开发完成**：22 工具 + Subagent + Hooks + Skill + Cron/Workflow/Worktree/Messaging，全量测试通过。
