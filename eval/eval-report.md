# mycode vs claude-code 对比评估报告

> 日期：2026-10-13 | 模型：qwen3-32b（ollama） | 评估框架版本：v1

## 1. 实验设置

### 1.1 评估方法论

采用 **inference/eval 解耦** 架构（借鉴 SWE-bench）：

```
[任务集 12题] --→ mycode    --→ 工作目录变更 + stdout
      \--→ claude-code --→ 工作目录变更 + stdout
                                    ↓
                    [统一评分器] --→ 分数对比
```

- 两个 harness 只负责执行任务、产出文件变更
- 评分器独立于 harness，做客观判定（测试通过 / 文件比对 / 正则匹配）
- 不使用 LLM-as-judge，避免主观偏置

### 1.2 环境控制

| 控制变量 | 值 | 说明 |
|---------|-----|------|
| 模型 | qwen3-32b | 同一 ollama 模型 |
| API 端点 | http://localhost:11434 | ollama 原生 Anthropic 兼容端点 |
| 温度 | 模型默认 | 两个 harness 不额外设温度 |
| 超时 | 120s/任务 | 超时记为失败 |
| 工作目录 | 每任务×每harness 独立 | 互不污染 |
| 权限 | 全自动 | mycode: --permission-mode auto; claude: --dangerously-skip-permissions |
| 配置隔离 | CLAUDE_CONFIG_DIR=/tmp/claude-cfg | 避免 ~/.claude/settings.json env 覆盖 |

### 1.3 任务集

12 个任务，3 个难度级别：

| 难度 | 数量 | 任务类型 |
|------|------|---------|
| Easy | 4 | 文件读取、Glob 搜索、简单代码生成、文本替换 |
| Medium | 4 | Bug 修复、多文件汇总、Shell 解析、代码重构 |
| Hard | 4 | 项目分析、工具链任务、调试测试、设计实现 |

### 1.4 评分方法

| 方法 | 适用 | 判定 |
|------|------|------|
| test_pass | 代码任务 | 在工作目录执行测试代码，stdout 含 PASS |
| file_match | 文件产出任务 | 比对产出文件内容与期望一致 |
| regex/regex_all | 分析类任务 | 在输出/文件中搜索关键模式 |
| files_exist | 多文件创建任务 | 检查文件存在 + 内容含指定字符串 |

## 2. 总体结果

| 指标 | mycode | claude-code |
|------|--------|-------------|
| **通过率** | **11/12 (91.7%)** | **11/12 (91.7%)** |
| 平均耗时 | **11.2s** | 60.2s |
| Easy | 4/4 | 4/4 |
| Medium | 4/4 | 3/4 |
| Hard | 3/4 | 4/4 |

**关键发现**：通过率相同（11/12），但**失败的题目不同**——两个 harness 具有互补性。mycode 平均快 **5.4 倍**。

## 3. 逐题对比

| 任务 | 难度 | mycode | claude | mycode 耗时 | claude 耗时 |
|------|------|--------|--------|-----------|-----------|
| e1_file_read | easy | ✓ | ✓ | 6.14s | 24.20s |
| e2_glob_search | easy | ✓ | ✓ | 6.15s | 35.42s |
| e3_simple_code | easy | ✓ | ✓ | 9.10s | 48.09s |
| e4_text_replace | easy | ✓ | ✓ | 6.11s | 39.54s |
| m1_bug_fix | medium | ✓ | ✓ | 9.35s | 76.07s |
| m2_multi_file | medium | ✓ | ✓ | 7.57s | 62.06s |
| **m3_shell_parse** | medium | **✓** | **✗** | 17.66s | 120s(超时) |
| m4_refactor | medium | ✓ | ✓ | 9.63s | 52.27s |
| **h1_project_analyze** | hard | **✗** | **✓** | 11.19s | 120s |
| h2_tool_chain | hard | ✓ | ✓ | 10.37s | 52.67s |
| h3_debug_test | hard | ✓ | ✓ | 28.05s | 39.93s |
| h4_design_impl | hard | ✓ | ✓ | 12.50s | 51.66s |

## 4. 失败案例分析

### 4.1 m3_shell_parse — claude-code 失败（超时）

**任务**：执行 `python3 -c "print(list(range(1,21)))"` 提取偶数写入 evens.txt

**claude-code**：超时 120s。claude-code 的 agent loop 开销大（system prompt 11 段 + 21 工具 schema），对于简单 shell 任务存在"杀鸡用牛刀"问题。ollama 本地模型推理速度有限，claude-code 多轮调用的累积延迟导致超时。

**mycode**：17.66s 通过。mycode 的轻量 harness 减少了不必要的开销。

**启示**：harness 轻重影响简单任务的效率。claude-code 的重量级 harness 在本地小模型上有劣势。

### 4.2 h1_project_analyze — mycode 失败

**任务**：分析项目结构，生成 analysis.md 报告（文件列表 + 行数 + 函数名）

**mycode**：11.19s 完成，但报告只匹配 1/9 个模式。mycode 可能没有完整读取所有文件，或报告格式不符合评分要求。

**claude-code**：120s（刚好卡在超时边界），匹配 7/9 个模式通过。claude-code 的 system prompt 中有"分析项目结构"的指导，更擅长此类多步骤分析任务。

**启示**：mycode 在多文件分析类任务上需要加强——可能需要更好的 system prompt 引导或工具调用策略。

## 5. 效率对比

| 指标 | mycode | claude-code | 比值 |
|------|--------|-------------|------|
| 平均耗时 | 11.2s | 60.2s | mycode 快 5.4× |
| 最快任务 | 6.11s | 24.20s | mycode 快 4.0× |
| 最慢任务 | 28.05s | 120s(超时) | — |
| Easy 平均 | 6.9s | 36.8s | mycode 快 5.3× |
| Medium 平均 | 11.1s | 77.6s* | mycode 快 7.0× |
| Hard 平均 | 15.5s | 65.8s | mycode 快 4.2× |

*claude medium 含一个超时，按 120s 计

**效率优势来源**：
- mycode 的 system prompt 更短（无 11 段冗长 system prompt）
- mycode 工具 schema 更少（按需注册 vs claude-code 21 个全量注册）
- mycode agent loop 轮数更少（轻量 harness 减少不必要的思考/规划轮）

## 6. 结论

### 6.1 总体评价

| 维度 | mycode | claude-code |
|------|--------|-------------|
| 正确性 | 91.7% | 91.7% |
| 效率 | ★★★★★ | ★★☆ |
| 简单任务 | 优 | 良（偏慢） |
| 中等任务 | 优 | 良（有超时） |
| 复杂分析 | 良 | 优 |
| 稳定性 | 待多轮验证 | 待多轮验证 |

### 6.2 互补性

两个 harness 失败的题目不同，说明：
- **mycode 优势**：轻量、快速、简单/中等任务效率高
- **claude-code 优势**：多文件分析、复杂规划任务更全面
- **潜在改进**：mycode 可借鉴 claude-code 的分析类 system prompt；claude-code 可优化轻量任务的调用开销

### 6.3 后续建议

1. **Pass^k 验证**：每个任务跑 3-5 次，计算 Pass^k，消除单次随机性
2. **多模型对比**：用 deepseek-r1-32b 再跑一遍，看 harness 差异是否跨模型稳定
3. **扩展任务集**：增加更多 hard 任务（多步调试、跨文件重构、设计模式实现）
4. **mycode 改进**：分析 h1 失败原因，加强分析类任务的 system prompt
5. **效率归因**：拆解 claude-code 的 60s 耗时——多少在 ollama 推理、多少在 harness 开销

## 7. 评估框架

| 文件 | 说明 |
|------|------|
| `eval/tasks.py` | 12 个任务定义（prompt + setup + scoring） |
| `eval/scorer.py` | 统一评分器（test_pass/file_match/regex/files_exist） |
| `eval/run_eval.py` | 运行器 + 主入口（支持 --model/--difficulty/--harnesses） |
| `eval/results/` | 结果存储（JSON + 工作目录快照） |

复用方法：
```bash
# 全量对比
python3 eval/run_eval.py --model qwen3-32b --difficulty all

# 只跑 hard 难度
python3 eval/run_eval.py --model qwen3-32b --difficulty hard

# 换模型
python3 eval/run_eval.py --model deepseek-r1-32b --difficulty all
```