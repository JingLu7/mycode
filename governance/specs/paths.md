# 知识路径

路径表达知识属于哪个领域、适用于哪种逆向目标，以及采用哪种路径 Profile。Concept ID 是路径相对 `knowledge/` 去掉 `.md` 后的值。

## 基本形态

```text
knowledge/<domain>/<technology-or-scope>/<profile>/[<section>/...]<slug>.md
```

- Concept ID 不带开头 `/`、`knowledge/` 前缀或 `.md` 后缀。
- 文件名使用小写 `snake_case`。

## Domain 与 route

| Domain | Technology/scope route | 说明 |
|---|---|---|
| `recon` | `claude-code`, `codex`, `atomcode`, `shared` | 按逆向目标隔离；`shared` 放跨目标通用知识 |
| `dev` | 无直接 route | mycode 自身开发知识，直接用 Profile |
| `common` | 无直接 route | 通用知识，直接用 Profile |

route 后必须出现路径 Profile。

## 路径 Profile

| Profile | OKF type | 保存内容 |
|---|---|---|
| `concepts/` | Concept | 稳定概念、结构模型、协议设计 |
| `apis/` | API | 接口签名、参数、headers 和工具 schema |
| `runbooks/` | Runbook | 按症状或任务组织的操作步骤与踩坑处置 |
| `guides/` | Guide | 围绕开发任务组织的原理与步骤 |
| `glossaries/` | Glossary | 术语与定义 |

## Index 导航

- 只有 `knowledge/index.md` 带 `okf_version: "0.2"` frontmatter；其他索引不带 frontmatter。
- 每个目录都必须有 `index.md`，完整列出直接子目录和知识卡，附简短摘要。
- `index.md` 不参与知识检索。

## 示例

```text
knowledge/recon/claude-code/concepts/agent_loop_protocol.md
knowledge/recon/claude-code/apis/request_parameters.md
knowledge/recon/shared/runbooks/sse_stream_requirement.md
knowledge/dev/concepts/architecture.md
```