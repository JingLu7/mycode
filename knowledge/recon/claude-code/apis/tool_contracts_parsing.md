---
name: tool-contracts-parsing
description: 从 sdk-tools.d.ts 白盒解析全量工具契约的方法与结果
type: concept
created: 2026-10-13
tags: [claude-code, tools, reverse-engineering, dts]
---

# sdk-tools.d.ts 工具契约解析

## 权威工具名来源（关键）

`ToolInputSchemas` **union type**（d.ts line 11-56）——**union 成员才是工具名**。
不要按文件内 `export interface` 数量统计（会把子接口/别名一起算进去，导致数字虚高）。

## 解析方法（零网络，纯静态）

1. 提取 union：正则 `export type ToolInputSchemas =(.*?);` → `\|\s*(\w+)` 取成员
2. 定位 `export interface (\w+)Input {`，用**花括号计数**取块体（不能简单按 `}` 切，类型里有嵌套）
3. 块体内正则提取字段：
   `(?:/\*\*(?P<doc>.*?)\*/)?\s*(?P<name>"[^"]+"|[\w$]+)\s*(?P<opt>\?)?:\s*(?P<type>[^;]+);`
4. **无 `?` 即 required**
5. Output：检测 `export (interface|type) (\w+)Output` 存在性

脚本：`tools/recon/dump_tool_contracts.py`
产出：`artifacts/recon/tool-contracts.json`

## 结果（2026-10-13 实测）

| 口径 | 数量 |
|------|------|
| union 成员（契约） | 44 |
| 运行时 `-p` 捕获 | 20 |
| 契约有但运行时无 | 27 |
| 运行时有但契约无 | 3（SendMessage/ListAgents/Skill） |

## 关键坑：d.ts 命名 ≠ 运行时工具名

- d.ts: `FileRead` / `FileEdit` / `FileWrite` ↔ 运行时: `Read` / `Edit` / `Write`
- 解析后必须做**命名归一**（去 `File` 前缀），否则差异表会误报 3 个"缺失"

## 与 mycode 的对齐状态（R2 已完成 2026-10-13）

| 工具 | d.ts 契约 | mycode 状态 |
|------|----------|------------|
| `Read` | `pages`(PDF 页范围) + `allow_large` | ✅ 已对齐（PDF 走系统 `pdftotext`） |
| `Grep` | 15 字段 | ✅ 已对齐（output_mode/-A/-B/-C/context/-n/-i/-o/glob/type/head_limit/offset/multiline） |
| `TodoWrite` | `todos`/`status`/`activeForm` | ✅ 新增 |
| `Glob` | `pattern`/`path` | ✅ 一致 |

验证脚本：`tests/verify_r2_tools.py`（19 项全过，含真实 PDF `pages=1`）。