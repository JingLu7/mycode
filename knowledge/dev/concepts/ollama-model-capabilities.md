---
name: ollama-model-capabilities
description: ollama 0.34.3 模型能力实测——num_ctx 默认行为、thinking 支持、并行显存占用、thinking+tool 同时、多轮消息格式
type: concept
created: 2026-10-15
tags: [mycode, ollama, model, thinking, num_ctx, vram]
---

# ollama 模型能力实测（0.34.3）

硬件：RTX 4090D / 48GB 显存。全部数据为 `/api/show`、`/api/ps`、`/api/chat` 实测。

## 模型能力矩阵

| 模型 | thinking | tools | 原生 ctx | @256K 显存 | @32K 显存 | think+tool 同时 |
|------|----------|-------|----------|-----------|-----------|----------------|
| qwen3.8-27b | ✅ | ✅ | 262144 | 33.1GB | 18.0GB | ✅ **可行** |
| qwen3.5-9b | ✅ | ✅ | 262144 | 14.1GB | 6.5GB | ✅ |
| qwen3-coder-30b | ❌ | ✅ | 262144 | — | ~19GB | ❌ think=True 返回空 |
| qwen3-32b | ✅ | ✅ | 40960 | — | — | — |
| deepseek-r1-32b | ✅ | ✅ | 131072 | — | — | — |

## 关键发现

### 1. num_ctx 默认拉满到模型最大值（非小值）

ollama 0.34.3 **默认 `num_ctx` = 模型原生 context_length**（如 256K），不是旧版的 2048/4096。
后果：KV cache 随 ctx 线性增长，27b @256K 吃 **33.1GB** 显存。
**必须显式设 `options.num_ctx`** 才能控制显存。实测：27b @32K 仅 18.0GB。

**按角色分配 num_ctx**（用户方案，48GB 满用不留空）：
- 主模型 qwen3.8-27b：`num_ctx=262144`（256K，33.1GB）
- 子 agent qwen3.5-9b：`num_ctx=32768`（32K，6.5GB）
- 合计 39.6GB / 48GB，**两模型并行共存实测可行**（`/api/ps` 显示都在）

### 2. thinking 与 tool-calling 可同时（27b）

qwen3.8-27b 传 `think: true` + `tools` 时，**同一个 message 同时返回 `thinking` 和 `tool_calls`**：
```json
{"role":"assistant","content":"","thinking":"...","tool_calls":[{"function":{"name":"get_weather","arguments":{"city":"北京"}}}]}
```
对比：旧模型 qwen3-32b 必须 `think:false` 才返回 tool_calls。qwen3.8-27b 无需此妥协。

### 3. qwen3-coder-30b 不支持 thinking

`capabilities` 只有 `['tools','completion']`（无 `thinking`）。传 `think:true` **直接返回空**（0.0s、无 content 无 tool_calls）。
结论：coder 必须 `think:false`；不用它做主模型（无法开 thinking）。

### 4. 多轮 tool-calling 消息格式（全量保留的依据）

ollama `/api/chat` 的消息格式：
- assistant 消息：`{role:'assistant', content:'', thinking:'...', tool_calls:[{function:{name, arguments}}]}`
- 工具结果：`{role:'tool', content:'<结果>'}`（**不是** `role:user`）

实测：轮1 返回 thinking+tool_calls → 轮2 回填 `assistant(thinking+tool_calls)` + `tool(结果)` → 模型正确生成最终回答。

**mycode `_convert_messages` 须全量保留**：thinking→`thinking` 字段、tool_use→`tool_calls`、tool_result→`role:tool`，不丢弃任何块（旧实现 `pass` 掉 tool_use 是缺陷）。

## 对 mycode 的配置约定

- 主 agent：`qwen3.8-27b`，`--num-ctx 262144`，thinking 开
- 子 agent：`qwen3.5-9b`，`num_ctx=32768`，thinking 开
- coder（备用）：`--no-think`
- 所有模型需显式 `num_ctx`，勿依赖 ollama 默认（会拉满）