# AtomCode 逆向

atomcode 逆向知识入口。2026-10-23 启动，B 路线（mock 端点抓取）已完成首轮捕获。

## 产出位置

逆向证据在 `artifacts/recon/atomcode/`，知识卡在本目录下。

## 已沉淀知识卡

- [harness 结构与请求协议](concepts/harness_structure.md) — 二进制本质、B 路线抓取方法、system prompt 22 段结构、与 claude-code 对比
- [工具目录](apis/tool_catalog.md) — 28 个工具定义、与 claude-code 工具集对比、定位差异
- [agent loop 协议](apis/agent_loop_protocol.md) — OpenAI 格式 tool_calls/tool_result、沙箱限制、system-reminder 机制

## 关键发现

- atomcode 是 C/C++ 编译的原生 ELF（46MB stripped），非 Bun/JS
- 用 OpenAI 兼容接口（`/v1/chat/completions`），非 Anthropic 格式
- system prompt 36810 字符（22 段），比 claude-code 长 6 倍
- 28 个工具，含 8 个代码分析工具（符号/调用图/依赖管理）
- agent loop 用 OpenAI 格式（tool_calls + role=tool），非 Anthropic 格式
- 有工作目录沙箱（文件访问限制在 cwd 内）
- 配置在 `~/.atomcode/config.toml`（TOML），provider 可重定向

## 逆向报告

- `docs/atomcode-reverse-engineering-report.md` — 完整逆向报告（8 章）

通用方法论复用 `recon/shared/`。
