---
type: Concept
title: mycode 架构形态决策
description: mycode 形态为贴近 claude-code 原栈 + 保留对外可复用接口（服务于别的项目）；首版交付物为 harness 逆向报告。
tags: [task.design, topic.architecture, topic.harness]
status: stable
sources: []
created_at: "2026-10-12T00:00:00Z"
updated_at: "2026-10-12T00:00:00Z"
platforms: [agnostic]
---

# mycode 架构形态决策

## 形态定位

mycode 贴近 **claude-code 原栈**（system prompt 结构、工具系统、agent loop 协议），同时保留**对外可复用接口**，可以服务于用户的其他项目。

## 设计依据

来自 claude-code 逆向发现：

- **system prompt 分段**：复用 `# Harness`、`# Memory`、`# Context management` 等分段设计。详见 [system prompt 结构](../../recon/claude-code/concepts/system_prompt_structure.md)。
- **agent loop 协议**：复用 5 条 messages 结构（user/system/assistant tool_use/user tool_result/system token预算）。详见 [agent loop 协议](../../recon/claude-code/concepts/agent_loop_protocol.md)。
- **工具系统**：参考 claude-code 的 20 个工具，按需裁剪或扩展。详见 [工具目录](../../recon/claude-code/apis/tool_catalog.md)。
- **请求参数**：参考 model、max_tokens、thinking、context_management 等参数设计。详见 [请求参数](../../recon/claude-code/apis/request_parameters.md)。

## 模型层

使用宿主 ollama 本地模型（qwen3-32b、deepseek-r1-32b），通过 `/api/chat` 接口对接。tool calling 须关 thinking。详见 [ollama thinking 坑](../../recon/shared/runbooks/ollama_thinking_tool_call.md)。

## 交付计划

1. **首版**：harness 逆向报告（文档，不写代码）。
2. **后续**：mycode 原型开发（贴近原栈 + 对外接口）。
3. **远期**：逆向 codex、atomcode，扩展知识库。