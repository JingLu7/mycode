"""Phase 2 测试实验 — 44 工具全量对齐

验证项：
  1. 44 个契约工具全部覆盖（builtin + contract_tools）
  2. mycode 契约外 3 工具（ListAgents/SendMessage/Skill）保留
  3. 24 个契约工具的 schema 完整（name/description/input_schema）
  4. 契约工具的参数名与 sdk-tools.d.ts 对齐（抽样：TaskCreate/AskUserQuestion）
  5. 实参 schema 合法（type=object、properties 非空）
"""
import sys
import json

sys.path.insert(0, "/data/taoming/project/mycode/src")
from mycode.tools.contract_tools import CONTRACT_TOOLS

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


print("=== Phase 2 测试实验：44 工具全量对齐 ===\n")

contracts = json.load(open("/data/taoming/project/mycode/artifacts/recon/tool-contracts.json"))
contract_tools = set(contracts["contract_tools"])

# mycode 原有 23 工具（与 cli/main.py 注册一致）
BUILTIN = {
    "Bash", "Read", "Write", "Edit", "Glob", "Grep", "WebFetch", "WebSearch",
    "NotebookEdit", "TaskStop", "Agent", "ListAgents", "Skill",
    "CronCreate", "CronDelete", "CronList", "EnterWorktree", "ExitWorktree",
    "SendMessage", "ReportFindings", "ScheduleWakeup", "Workflow", "TodoWrite",
}
all_tools = BUILTIN | set(CONTRACT_TOOLS.keys())

print(f"[1] 44 契约覆盖（契约 {len(contract_tools)} 个，mycode 共 {len(all_tools)} 个工具）")
missing = sorted(contract_tools - all_tools)
check("44 契约全覆盖", not missing, f"缺失: {missing}")

print("\n[2] 契约外工具保留")
for t in ["ListAgents", "SendMessage", "Skill"]:
    check(f"{t} 保留", t in all_tools)

print("\n[3] 24 契约工具 schema 完整")
for name, spec in CONTRACT_TOOLS.items():
    ok = all(k in spec for k in ("name", "description", "input_schema"))
    check(f"{name} 完整", ok, str(list(spec.keys())))

print("\n[4] 参数对齐抽样")
# TaskCreate: 契约有 subject/description/activeForm/metadata
tc_props = set(CONTRACT_TOOLS["TaskCreate"]["input_schema"]["properties"].keys())
expected_tc = {"subject", "description", "activeForm", "metadata"}
check("TaskCreate 参数对齐", expected_tc <= tc_props, f"got {tc_props}")
src_tc = contracts["tools"].get("TaskCreateInput", {}).get("input", {}).get("properties", {})
check("TaskCreate 参数数匹配契约", len(tc_props) == len(src_tc), f"mycode={len(tc_props)} contract={len(src_tc)}")

# AskUserQuestion: 顶层 questions 必填
aq = CONTRACT_TOOLS["AskUserQuestion"]["input_schema"]
check("AskUserQuestion 有 questions", "questions" in aq["properties"])
check("AskUserQuestion questions 必填", "questions" in aq.get("required", []))

print("\n[5] schema 合法性")
for name, spec in CONTRACT_TOOLS.items():
    s = spec["input_schema"]
    ok = s.get("type") == "object" and isinstance(s.get("properties"), dict)
    if not ok:
        check(f"{name} schema 合法", False, str(s)[:80])
check("全部契约工具 schema 为 object", all(
    CONTRACT_TOOLS[n]["input_schema"].get("type") == "object" for n in CONTRACT_TOOLS
))

print(f"\n=== 结果: {PASS} PASS / {FAIL} FAIL ===")
sys.exit(0 if FAIL == 0 else 1)