"""Phase 6 测试实验 — 子 agent 并行（spawn_all + 9b 子模型）

验证项：
  1. SubagentManager 支持 subagent_model / subagent_num_ctx 配置
  2. spawn 用子模型（非主模型）
  3. spawn_all 并行启动多个 subagent
  4. 子 agent 的 OllamaProvider 用正确参数
"""
import sys
import json
from unittest.mock import patch, MagicMock

sys.path.insert(0, "/data/taoming/project/mycode/src")
from mycode.harness.subagent import SubagentManager
from mycode.llm.ollama import OllamaProvider

PASS = 0
FAIL = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS  {name}")
    else:
        FAIL += 1
        print(f"  FAIL  {name}  {detail}")


print("=== Phase 6 测试实验：子 agent 并行 ===\n")

# ── 1. 配置参数 ──
print("[1] 子模型配置")
sm = SubagentManager()
sm.configure(
    llm=MagicMock(spec=OllamaProvider),
    tools=MagicMock(),
    system_prompt="SYS",
    subagent_model="qwen3.5-9b",
    subagent_num_ctx=32768,
)
check("子模型=qwen3.5-9b", sm._subagent_model == "qwen3.5-9b")
check("子 num_ctx=32768", sm._subagent_num_ctx == 32768)

# ── 2. spawn 用子模型 ──
print("\n[2] spawn 用子模型（mock OllamaProvider）")
with patch("mycode.llm.ollama.OllamaProvider") as MockOllama:
    mock_llm = MagicMock()
    mock_llm.base_url = "http://localhost:11434"
    MockOllama.return_value = mock_llm

    sm.configure(
        llm=MagicMock(spec=OllamaProvider),
        tools=MagicMock(),
        system_prompt="SYS",
        subagent_model="qwen3.5-9b",
        subagent_num_ctx=32768,
    )

    # mock AgentLoop.run 返回固定结果
    with patch("mycode.agent.loop.AgentLoop") as MockLoop:
        mock_loop = MagicMock()
        mock_loop.run.return_value = "[Subagent agent-abc123 (general) completed]\nresult"
        MockLoop.return_value = mock_loop

        result = sm.spawn("prompt", "general", "desc")
        check("spawn 返回结果", "completed" in result)
        check("OllamaProvider 用子模型", MockOllama.call_args.kwargs.get("model") == "qwen3.5-9b")
        check("OllamaProvider 用子 num_ctx", MockOllama.call_args.kwargs.get("num_ctx") == 32768)

# ── 3. spawn_all 并行 ──
print("\n[3] spawn_all 并行")
sm2 = SubagentManager()
sm2.configure(
    llm=MagicMock(spec=OllamaProvider),
    tools=MagicMock(),
    system_prompt="SYS",
    subagent_model="qwen3.5-9b",
    subagent_num_ctx=32768,
)
with patch("mycode.llm.ollama.OllamaProvider") as MockOllama2, \
     patch("mycode.agent.loop.AgentLoop") as MockLoop2:
    mock_llm2 = MagicMock()
    mock_llm2.base_url = "http://localhost:11434"
    MockOllama2.return_value = mock_llm2

    def _mock_run(prompt):
        return f"[Subagent agent-{hash(prompt) % 10000:04d} (general) completed]\nresult-{prompt[:5]}"

    mock_loop2 = MagicMock()
    mock_loop2.run.side_effect = _mock_run
    MockLoop2.return_value = mock_loop2

    tasks = [("task1", "general", "t1"), ("task2", "general", "t2"), ("task3", "coder", "t3")]
    results = sm2.spawn_all(tasks)
    check("spawn_all 返回 3 个结果", len(results) == 3)
    check("所有结果含 agent_id", all(r["agent_id"] != "unknown" for r in results))
    check("所有结果含 result", all("result" in r for r in results))

print(f"\n=== 结果: {PASS} PASS / {FAIL} FAIL ===")
sys.exit(0 if FAIL == 0 else 1)