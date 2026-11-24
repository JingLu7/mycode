---
type: Concept
title: claude-code 2.1.296 的 harness 物理结构
description: claude-code@2.1.296 是 Bun --compile 产出的原生 ELF 单文件（246MB），应用 JS 以 JSC bytecode 内嵌（非明文），字符串常量明文可提取。
tags: [task.reverse_engineering, topic.harness, topic.architecture]
status: stable
sources:
  - resource: artifacts/recon/capture-full-mode.json
    role: evidence
  - resource: /home/zigaa/.local/lib/node_modules/@anthropic-ai/claude-code/bin/claude.exe
    role: implementation
created_at: "2026-10-12T00:00:00Z"
updated_at: "2026-10-12T00:00:00Z"
platforms: [agnostic]
target_versions: ["claude-code@2.1.296"]
---

# claude-code 2.1.296 的 harness 物理结构

## 二进制本质

`bin/claude.exe` 是 **Bun `--compile` 产出的原生 ELF 单文件**，不是早期版本的 JS bundle。

| 属性 | 值 |
|------|-----|
| 大小 | 246 MB |
| 格式 | ELF 64-bit LSB executable |
| stripped | no（仅动态符号表 ~1230 项） |
| 特殊段 | `.bun_builtins` |
| 运行时 | Bun runtime + JSC 引擎 |

## 应用代码嵌入方式

应用 JS 以 **JSC bytecode** 内嵌，不是明文源码。反编译 `.text` 段只能得到 Bun runtime 和 JSC 引擎的 C++ 代码，**拿不到应用层逻辑**（在 bytecode 里）。

## 可提取的明文资产

| 资产 | 提取方式 | 内容 |
|------|---------|------|
| 字符串常量 | `strings bin/claude.exe` | system prompt 片段、工具名、环境变量名、错误消息 |
| 工具契约 | `sdk-tools.d.ts`（171KB） | 43 个工具的 TypeScript 类型定义 |
| 环境变量 | `strings \| grep CLAUDE_CODE_` | `CLAUDE_CODE_*` 前缀的变量名 |

## 逆向路线影响

- **静态字符串提取（A 路线）**：可行，能拿到碎片化的 prompt 片段和工具名，但不完整。
- **动态请求抓取（B 路线）**：可行且完整，通过 mock 端点拿到完整 system prompt + tools + 参数。详见 [mock 端点抓取](../shared/runbooks/mock_endpoint_capture.md)。
- **native 反编译（C 路线）**：只能拿到 Bun/JSC 引擎，无应用逻辑，价值有限。
- **白盒契约（D 路线）**：`sdk-tools.d.ts` 提供工具接口契约，可交叉验证 B 路线结果。