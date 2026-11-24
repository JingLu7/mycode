---
type: Concept
title: agent CLI 逆向工程四条路线
description: 静态字符串提取（A）、动态请求抓取（B）、native 反编译（C）、白盒契约（D）四条逆向路线的可行性、产出和价值评估。
tags: [task.reverse_engineering, topic.methodology, topic.harness]
status: stable
sources: []
created_at: "2026-10-12T00:00:00Z"
updated_at: "2026-10-12T00:00:00Z"
platforms: [agnostic]
---

# agent CLI 逆向工程四条路线

逆向 agent CLI（如 claude-code、codex、atomcode）的 harness 与 agent loop 时，有四条路线。

## 路线 A：静态字符串提取

| 项 | 内容 |
|----|------|
| 方法 | `strings binary \| grep ...` |
| 产出 | 碎片化的 prompt 片段、工具名、环境变量名、错误消息 |
| 优点 | 零依赖，快速 |
| 局限 | 不完整，无法拿到工具 schema、请求参数、消息协议 |
| 适用 | 快速侦察，发现环境变量线索 |

## 路线 B：动态请求抓取

| 项 | 内容 |
|----|------|
| 方法 | 写 mock 端点，用 `ANTHROPIC_BASE_URL`（或等价环境变量）把 CLI 的 API 出口指过去 |
| 产出 | 完整 system prompt、tools schema、请求参数、headers、agent loop messages |
| 优点 | 完整、可靠、可编程驱动 |
| 局限 | 需要目标 CLI 支持 base URL 重定向；mock 必须返回 SSE 流式响应 |
| 适用 | 逆向 harness 和 agent loop 的首选路线 |

详见 [mock 端点抓取方法](../runbooks/mock_endpoint_capture.md)。

## 路线 C：native 反编译

| 项 | 内容 |
|----|------|
| 方法 | 反编译 ELF `.text` 段 |
| 产出 | Bun runtime + JSC 引擎的 C++ 代码 |
| 优点 | 理论上可拿到所有逻辑 |
| 局限 | 对 Bun `--compile` 产物，应用 JS 是 JSC bytecode，反编译 `.text` 拿不到应用逻辑 |
| 适用 | 价值有限，不推荐作为主路线 |

## 路线 D：白盒契约

| 项 | 内容 |
|----|------|
| 方法 | 读取 `sdk-tools.d.ts` 等类型声明文件 |
| 产出 | 工具接口的 TypeScript 类型定义 |
| 优点 | 精确的接口契约 |
| 局限 | 只有工具签名，没有 system prompt、请求参数、消息协议 |
| 适用 | 交叉验证 B 路线结果 |

## 推荐组合

**A + B + D**：A 做快速侦察（发现环境变量线索），B 做完整抓取（system prompt + tools + 协议），D 做交叉验证（工具契约）。C 对 Bun 产物价值有限，跳过。

## 对 codex/atomcode 的适用性

- B 路线：codex 和 atomcode 如果支持 base URL 重定向（如 `OPENAI_BASE_URL`），同样适用。
- A 路线：通用，任何二进制都可 `strings`。
- D 路线：取决于目标是否发布类型声明文件。
- C 路线：取决于目标的打包方式（如果是 Bun/Deno compile，同样价值有限）。