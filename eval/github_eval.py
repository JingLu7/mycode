"""搜集 GitHub 评测项目任务 — 对比测试。

用已有的 subagent 调研结果作为参考答案，分别让 claude code 和 mycode 跑同一任务，
对比输出质量。
"""
import os
import sys
import json
import time
import shutil
import subprocess

sys.path.insert(0, "/data/taoming/project/mycode/eval")
from run_eval import run_mycode, run_claude, RESULTS_DIR

# 任务 prompt（与之前给 subagent 的核心意图一致）
TASK_PROMPT = """请搜集 GitHub 上高 star 的 AI agent 评测/benchmark 项目，返回结构化调研报告。

具体要求：
1. 搜索 GitHub 上与 agent benchmark、agent evaluation、coding agent benchmark 相关的高 star 项目
2. 对每个找到的项目，记录：项目名、star 数、评测方法论
3. 特别关注那些做"同一模型 + 不同 agent harness 对比"的项目
4. 返回结构化调研报告，包含：找到的项目列表、评测方法论摘要、推荐方法

请用中文返回结果。"""

# 参考答案中的关键项目和方法论（用于评分）
KEY_PROJECTS = [
    "SWE-bench", "SWE-bench",
    "AgentBench",
    "tau-bench", "τ-bench",
    "human-eval", "HumanEval",
    "inspect_ai", "inspect-ai",
    "SWE-agent",
    "OpenHands",
    "aider",
    "ToolBench",
    "OSWorld",
    "terminal-bench",
]

KEY_METHODOLOGY = [
    "inference/eval 解耦",
    "Pass^k", "pass@k",
    "Docker",
    "可执行测试",
    "pass@k",
    "客观判定",
    "容器化",
]


def score_output(output):
    """评分：在输出中搜索关键项目和方法论关键词。"""
    output_lower = output.lower()
    
    # 项目覆盖
    projects_found = []
    for p in KEY_PROJECTS:
        if p.lower() in output_lower:
            projects_found.append(p)
    projects_unique = list(set(projects_found))
    
    # 方法论覆盖
    methodology_found = []
    for m in KEY_METHODOLOGY:
        if m.lower() in output_lower:
            methodology_found.append(m)
    methodology_unique = list(set(methodology_found))
    
    # 评分
    project_score = min(len(projects_unique) / 5, 1.0)  # 找到 5 个即满分
    method_score = min(len(methodology_unique) / 3, 1.0)  # 找到 3 个即满分
    total_score = (project_score + method_score) / 2
    
    return {
        "score": round(total_score, 2),
        "projects_found": projects_unique,
        "projects_count": len(projects_unique),
        "methodology_found": methodology_unique,
        "methodology_count": len(methodology_unique),
    }


def run_comparison(model="qwen3-32b", timeout=300):
    """跑对比测试。"""
    print(f"\n{'='*60}")
    print(f"任务: 搜集 GitHub 评测项目 | 模型: {model}")
    print(f"超时: {timeout}s")
    print(f"{'='*60}\n")
    
    results = {}
    
    for harness_name, run_fn in [("mycode", run_mycode), ("claude", run_claude)]:
        ws = os.path.join(RESULTS_DIR, "workspaces", f"github_eval_{harness_name}")
        if os.path.exists(ws):
            shutil.rmtree(ws)
        os.makedirs(ws, exist_ok=True)
        
        print(f"→ {harness_name}...", end=" ", flush=True)
        run_result = run_fn(TASK_PROMPT, ws, model, timeout)
        
        # 评分
        scoring = score_output(run_result["stdout"])
        
        results[harness_name] = {
            "elapsed": run_result["elapsed"],
            "returncode": run_result["returncode"],
            "stdout_len": len(run_result["stdout"]),
            "stdout": run_result["stdout"][:5000],  # 保留前 5000 字符
            "stderr": run_result["stderr"][:500],
            "scoring": scoring,
        }
        
        s = scoring
        print(f"{s['score']:.2f} ({run_result['elapsed']}s)")
        print(f"  项目覆盖: {s['projects_count']} 个 — {s['projects_found'][:5]}")
        print(f"  方法论: {s['methodology_count']} 个 — {s['methodology_found'][:3]}")
        print()
    
    # 对比
    print(f"{'='*60}")
    print("对比结果")
    print(f"{'='*60}\n")
    
    for h, r in results.items():
        s = r["scoring"]
        print(f"  {h}:")
        print(f"    评分: {s['score']:.2f}")
        print(f"    耗时: {r['elapsed']}s")
        print(f"    输出长度: {r['stdout_len']} 字符")
        print(f"    项目覆盖: {s['projects_count']}/{len(KEY_PROJECTS)} — {s['projects_found']}")
        print(f"    方法论: {s['methodology_count']}/{len(KEY_METHODOLOGY)} — {s['methodology_found']}")
        print()
    
    # 保存
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    result_file = os.path.join(RESULTS_DIR, f"github-eval-{model}-{timestamp}.json")
    with open(result_file, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"结果已保存: {result_file}")
    
    # 保存完整输出
    for h, r in results.items():
        out_file = os.path.join(RESULTS_DIR, f"github-eval-{h}-{timestamp}.txt")
        with open(out_file, "w") as f:
            f.write(r.get("stdout", ""))
        print(f"{h} 完整输出: {out_file}")
    
    return results


if __name__ == "__main__":
    model = sys.argv[1] if len(sys.argv) > 1 else "qwen3-32b"
    timeout = int(sys.argv[2]) if len(sys.argv) > 2 else 300
    run_comparison(model, timeout)