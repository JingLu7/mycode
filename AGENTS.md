# mycode Agent 工作约定

本文件约束在 mycode 仓工作的自动化 Agent。

## 工作边界

- `knowledge/` 是唯一知识正文根，也是唯一 OKF Bundle root。不要在其他目录保存逆向发现、踩坑经验或设计决策。
- `knowledge/` 中除 `index.md` 外的 Markdown 都是 OKF Concept document；Frontmatter `type` 是其 OKF 类型。
- `governance/`、`logs/` 是治理与日志设施，不属于 OKF Bundle。
- `artifacts/` 是逆向产出（抓取的请求体等），作为证据文件被知识卡引用。
- 只修改当前任务需要的文件。开始前检查工作区，保留用户已有修改。
- 未经用户明确要求，不执行 commit、push。

## 知识体系结构

- **domain**：`recon`（逆向工程）、`dev`（mycode 开发）、`common`（通用）
- **recon 的 route**：`claude-code`、`codex`（预留）、`atomcode`（预留）、`shared`（跨目标通用）
- **路径 Profile**：`concepts/`、`apis/`、`runbooks/`、`guides/`、`glossaries/`
- 详见 `governance/specs/paths.md`

## 修改知识卡

1. 按 `governance/specs/paths.md` 选择 domain、route 和路径 Profile。
2. 按 `governance/specs/frontmatter.md` 填写 frontmatter。
3. `recon/shared/` 下的知识对 claude-code、codex、atomcode 三个目标都适用，确保通用性。
4. 新增卡片时同步受影响的每一级 `index.md`。

## 日志

- 实质知识或治理变更写入当天 `logs/YYYY-MM-DD.md`。
- 写日志前读取系统时钟：`date '+%Y-%m-%d %H:%M'`。
- 条目格式：`## [HH:MM] <operation> | 标题`，按时间倒序。

## 逆向目标

- **当前**：claude-code@2.1.296（B 路线已完成，产出在 `artifacts/recon/`）
- **后续**：codex、atomcode（预留位置在 `knowledge/recon/codex/`、`knowledge/recon/atomcode/`）
- **方法论**：A+B+D 组合（静态字符串 + 动态抓取 + 白盒契约），详见 `knowledge/recon/shared/concepts/reverse_engineering_routes.md`