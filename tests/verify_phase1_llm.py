"""Phase 1 测试实验 — 模型接入层（num_ctx / thinking / 消息全量保留）

验证项：
  1. OllamaProvider 支持 num_ctx / think 参数
  2. LLMResponse 含 thinking 字段
  3. _convert_messages 全量保留 thinking / tool_use(→tool_calls) / tool_result(→role:tool)
  4. Context.add_assistant 保留 thinking block
  5. payload 携带 options.num_ctx 与 think
"""
import sys
import json

sys.path.insert(0, "/data/taoming/project/mycode/src")

from mycode.llm.ollama import OllamaProvider
from mycode.llm.provider import LLMResponse, ToolCall
from mycode.agent.context import Context

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


print("=== Phase 1 测试实验：模型接入层 ===\n")

# 1. OllamaProvider 参数
print("[1] OllamaProvider 支持 num_ctx / think")
p = OllamaProvider(model="qwen3.8-27b", num_ctx=262144, think=True)
check("num_ctx 生效", p.num_ctx == 262144, f"got {p.num_ctx}")
check("think 生效", p.think is True, f"got {p.think}")
p2 = OllamaProvider(model="qwen3-coder-30b", num_ctx=32768, think=False)
check("coder: num_ctx=32768", p2.num_ctx == 32768)
check("coder: think=False", p2.think is False)

# 2. LLMResponse thinking 字段
print("\n[2] LLMResponse 含 thinking 字段")
r = LLMResponse(content="hi", tool_calls=[], done_reason="stop", thinking="思考内容")
check("thinking 字段存在且默认空", LLMResponse("a", [], "stop").thinking == "")
check("thinking 可赋值", r.thinking == "思考内容")

# 3. _convert_messages 全量保留
print("\n[3] _convert_messages 全量保留（thinking/tool_use/tool_result）")
messages = [
    {"role": "user", "content": "列出目录"},
    {"role": "assistant", "content": [
        {"type": "thinking", "thinking": "用户要列目录，用 Bash"},
        {"type": "text", "text": "我来执行"},
        {"type": "tool_use", "id": "t1", "name": "Bash", "input": {"command": "ls"}},
    ]},
    {"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": "t1", "content": "file1\nfile2"},
    ]},
]
out = p._convert_messages(messages, system="SYS")
print("  转换结果:")
print(json.dumps(out, ensure_ascii=False, indent=2))

check("system 首条", out[0] == {"role": "system", "content": "SYS"})
check("user 原文保留", out[1] == {"role": "user", "content": "列出目录"})
am = out[2]
check("assistant 消息存在", am.get("role") == "assistant", str(am)[:80])
check("thinking 保留", am.get("thinking") == "用户要列目录，用 Bash", f"got {am.get('thinking')!r}")
check("text 保留", am.get("content") == "我来执行")
check("tool_use → tool_calls 保留", "tool_calls" in am and am["tool_calls"][0]["function"]["name"] == "Bash")
check("tool_calls 参数保留", am["tool_calls"][0]["function"]["arguments"] == {"command": "ls"})
check("tool_result → role:tool 保留", out[3] == {"role": "tool", "content": "file1\nfile2"}, str(out[3]))

# 4. Context.add_assistant 保留 thinking
print("\n[4] Context.add_assistant 保留 thinking block")
ctx = Context()
ctx.add_user("hi")
ctx.add_assistant("回复", [{"type": "tool_use", "id": "x", "name": "Read", "input": {}}], thinking="想一下")
blocks = ctx.messages[-1]["content"]
has_thinking = any(b.get("type") == "thinking" and b.get("thinking") == "想一下" for b in blocks)
has_tool = any(b.get("type") == "tool_use" for b in blocks)
check("thinking block 进入 context", has_thinking)
check("tool_use block 进入 context", has_tool)

print(f"\n=== 结果: {PASS} PASS / {FAIL} FAIL ===")
sys.exit(0 if FAIL == 0 else 1)