"""评估运行器 — 同一试卷分别跑 mycode 和 claude-code，统一评分对比。

用法:
  python3 run_eval.py --model qwen3-32b --difficulty all
  python3 run_eval.py --model qwen3-32b --difficulty easy
"""
import os
import sys
import json
import time
import shutil
import argparse
import subprocess
import tempfile

sys.path.insert(0, os.path.dirname(__file__))
from tasks import TASKS, setup_workspace, get_tasks_by_difficulty
from scorer import score

MYCODE_CLI = "/data/taoming/project/mycode/src/mycode/cli/main.py"
CLAUDE_BIN = "claude"
OLLAMA_URL = "http://localhost:11434"
EVAL_ROOT = "/data/taoming/project/mycode/eval"
RESULTS_DIR = os.path.join(EVAL_ROOT, "results")

# 环境隔离：claude-code 用独立配置目录避免 ~/.claude/settings.json 的 env 覆盖
CLAUDE_ENV = {
    "CLAUDE_CONFIG_DIR": "/tmp/claude-cfg",
    "ANTHROPIC_BASE_URL": OLLAMA_URL,
    "ANTHROPIC_API_KEY": "dummy",
    "HOME": os.environ.get("HOME", "/home/zigaa"),
    "PATH": os.environ.get("PATH", ""),
}


MYCODE_ENV = {
    "PYTHONPATH": "/data/taoming/project/mycode/src",
    "HOME": os.environ.get("HOME", "/home/zigaa"),
    "PATH": os.environ.get("PATH", ""),
}


def run_mycode(prompt, workspace, model, timeout=120):
    """运行 mycode，返回 {stdout, stderr, returncode, elapsed}。"""
    start = time.time()
    try:
        result = subprocess.run(
            ["python3", MYCODE_CLI, "--model", model, "--base-url", OLLAMA_URL,
             "--permission-mode", "bypassPermissions", "--no-transcript", prompt],
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=MYCODE_ENV,
        )
        elapsed = time.time() - start
        return {
            "stdout": result.stdout,
            "stderr": result.stderr[:2000],
            "returncode": result.returncode,
            "elapsed": round(elapsed, 2),
        }
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "TIMEOUT", "returncode": -1, "elapsed": timeout}
    except Exception as e:
        return {"stdout": "", "stderr": str(e), "returncode": -2, "elapsed": round(time.time() - start, 2)}


def run_claude(prompt, workspace, model, timeout=120):
    """运行 claude-code，返回 {stdout, stderr, returncode, elapsed}。"""
    start = time.time()
    try:
        result = subprocess.run(
            ["claude", "--model", model, "-p", prompt, "--dangerously-skip-permissions"],
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=CLAUDE_ENV,
            stdin=subprocess.DEVNULL,
        )
        elapsed = time.time() - start
        return {
            "stdout": result.stdout,
            "stderr": result.stderr[:2000],
            "returncode": result.returncode,
            "elapsed": round(elapsed, 2),
        }
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "TIMEOUT", "returncode": -1, "elapsed": timeout}
    except Exception as e:
        return {"stdout": "", "stderr": str(e), "returncode": -2, "elapsed": round(time.time() - start, 2)}


def run_eval(model, difficulty="all", harnesses=None, timeout=120):
    """运行完整评估。"""
    if harnesses is None:
        harnesses = ["mycode", "claude"]
    
    tasks = get_tasks_by_difficulty(difficulty if difficulty != "all" else None)
    
    print(f"\n{'='*60}")
    print(f"评估基准: {len(tasks)} 个任务 | 模型: {model} | 难度: {difficulty}")
    print(f"Harness: {', '.join(harnesses)}")
    print(f"{'='*60}\n")
    
    results = []
    
    for i, task in enumerate(tasks):
        tid = task["id"]
        diff = task["difficulty"]
        print(f"[{i+1}/{len(tasks)}] {tid} ({diff})")
        
        task_result = {
            "task_id": tid,
            "difficulty": diff,
            "harnesses": {},
        }
        
        for harness in harnesses:
            # 为每个 harness 创建独立工作目录
            ws = os.path.join(RESULTS_DIR, "workspaces", f"{tid}_{harness}")
            if os.path.exists(ws):
                shutil.rmtree(ws)
            setup_workspace(task, ws)
            
            print(f"  → {harness}...", end=" ", flush=True)
            
            if harness == "mycode":
                run_result = run_mycode(task["prompt"], ws, model, timeout)
            elif harness == "claude":
                run_result = run_claude(task["prompt"], ws, model, timeout)
            else:
                continue
            
            # 评分
            scoring_result = score(task, ws, run_result["stdout"])
            
            hr = {
                "score": scoring_result["score"],
                "reason": scoring_result["reason"],
                "elapsed": run_result["elapsed"],
                "returncode": run_result["returncode"],
                "stdout_len": len(run_result["stdout"]),
                "stderr": run_result["stderr"][:500] if run_result["returncode"] != 0 else "",
            }
            task_result["harnesses"][harness] = hr
            
            status = "✓" if hr["score"] == 1 else "✗"
            print(f"{status} ({hr['elapsed']}s) {hr['reason'][:60]}")
        
        results.append(task_result)
    
    # 汇总
    print(f"\n{'='*60}")
    print("汇总")
    print(f"{'='*60}\n")
    
    summary = {"model": model, "difficulty": difficulty, "total": len(tasks), "harnesses": {}}
    
    for harness in harnesses:
        scores = [r["harnesses"][harness]["score"] for r in results if harness in r["harnesses"]]
        elapsed = [r["harnesses"][harness]["elapsed"] for r in results if harness in r["harnesses"]]
        by_diff = {}
        for diff in ["easy", "medium", "hard"]:
            diff_scores = [r["harnesses"][harness]["score"] for r in results 
                          if r["difficulty"] == diff and harness in r["harnesses"]]
            if diff_scores:
                by_diff[diff] = f"{sum(diff_scores)}/{len(diff_scores)}"
        
        summary["harnesses"][harness] = {
            "pass": sum(scores),
            "total": len(scores),
            "rate": f"{sum(scores)/len(scores)*100:.1f}%" if scores else "N/A",
            "avg_time": f"{sum(elapsed)/len(elapsed):.1f}s" if elapsed else "N/A",
            "by_difficulty": by_diff,
        }
        
        h = summary["harnesses"][harness]
        print(f"  {harness}: {h['pass']}/{h['total']} ({h['rate']}) | 平均耗时 {h['avg_time']} | 分难度: {h['by_difficulty']}")
    
    # 逐题对比
    print(f"\n逐题对比:")
    print(f"  {'任务':<25} {'难度':<8} {'mycode':<10} {'claude':<10} {'mycode时间':<12} {'claude时间':<12}")
    print(f"  {'-'*80}")
    for r in results:
        mc = r["harnesses"].get("mycode", {})
        cl = r["harnesses"].get("claude", {})
        mc_s = "✓" if mc.get("score") == 1 else "✗"
        cl_s = "✓" if cl.get("score") == 1 else "✗"
        mc_t = f"{mc.get('elapsed', '?')}s"
        cl_t = f"{cl.get('elapsed', '?')}s"
        print(f"  {r['task_id']:<25} {r['difficulty']:<8} {mc_s:<10} {cl_s:<10} {mc_t:<12} {cl_t:<12}")
    
    # 保存结果
    os.makedirs(RESULTS_DIR, exist_ok=True)
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    result_file = os.path.join(RESULTS_DIR, f"eval-{model}-{timestamp}.json")
    with open(result_file, "w") as f:
        json.dump({"summary": summary, "details": results}, f, indent=2, ensure_ascii=False)
    print(f"\n结果已保存: {result_file}")
    
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="mycode vs claude-code 对比评估")
    parser.add_argument("--model", default="qwen3-32b", help="ollama 模型名")
    parser.add_argument("--difficulty", default="all", choices=["all", "easy", "medium", "hard"])
    parser.add_argument("--harnesses", default="all", help="逗号分隔: mycode,claude 或 all")
    parser.add_argument("--timeout", type=int, default=120, help="每个任务超时秒数")
    args = parser.parse_args()
    
    harnesses = None if args.harnesses == "all" else args.harnesses.split(",")
    run_eval(args.model, args.difficulty, harnesses, args.timeout)