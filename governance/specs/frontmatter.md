# Frontmatter 与证据

## 公共必选字段

每张非 `index.md` 知识卡必须填写八个公共字段：

| 字段 | 用途 | 约束 |
|---|---|---|
| `type` | OKF 交换类型 | 非空，等于路径 Profile 的 `okf_type` |
| `title` | 人读标题 | 非空 |
| `description` | 摘要 | 非空 |
| `tags` | 工程任务和讨论主题 | 2–6 个，至少一个 `task.*` 和一个 `topic.*` |
| `status` | 生命周期 | `draft`、`stable` 或 `deprecated` |
| `sources` | 证据入口 | 数组；Runbook 可为空，其他非 draft 至少一项 |
| `created_at` | 首次创建时间 | UTC RFC 3339，`Z` 结尾 |
| `updated_at` | 最近实质变更时间 | 同上，不早于 `created_at` |

## Profile 字段组合

| 路径 Profile | OKF type | 额外必选 | 可选 |
|---|---|---|---|
| `concepts` | Concept | `platforms` | `target_versions`, `aliases`, `verified`, `replaced_by` |
| `apis` | API | `platforms` | `target_versions`, `aliases`, `verified`, `replaced_by` |
| `runbooks` | Runbook | `platforms` | `aliases`, `verified`, `replaced_by` |
| `guides` | Guide | `platforms` | `target_versions`, `aliases`, `verified`, `replaced_by` |
| `glossaries` | Glossary | 无 | `aliases`, `verified`, `replaced_by` |

## 生命周期

| `status` | 含义 |
|---|---|
| `draft` | 尚未评审或来源不足 |
| `stable` | 可在声明范围内消费 |
| `deprecated` | 历史引用保留，不再代表当前结论 |

## 来源（sources）

```yaml
sources:
  - resource: https://example.com/document
    role: primary
```

role 取值：`primary`、`supporting`、`example`、`constraint`、`header`、`implementation`、`evidence`。

逆向踩坑的 Runbook 可使用 `sources: []`，正文中的触发、症状、根因和验证信号就是可消费证据。

## 标签（tags）

至少一个 `task.*` 和一个 `topic.*`，来自 `registries.yaml` 注册值。不要堆叠弱相关标签。

## 适用范围

- 除 `glossaries` 外都要求 `platforms`。平台无关写 `[agnostic]`。
- `target_versions` 声明逆向目标版本边界（如 `claude-code@2.1.296`）。