#!/usr/bin/env python3
"""Phase 2: 从 sdk-tools.d.ts 生成 24 个缺失工具的 JSON Schema（参数/描述全量对齐）。

d.ts 由 json-schema-to-typescript 从 JSON Schema 反向生成，字段级 name/type/description 完整。
本脚本复用 tool-contracts.json 的解析结果，把 TS 类型转回 JSON Schema，
生成 src/mycode/tools/contract_tools.py。

用法: python3 tools/recon/gen_contract_tools.py
"""
from __future__ import annotations
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DTS = Path("/home/zigaa/.local/lib/node_modules/@anthropic-ai/claude-code/sdk-tools.d.ts")
CONTRACTS = ROOT / "artifacts" / "recon" / "tool-contracts.json"
OUT = ROOT / "src" / "mycode" / "tools" / "contract_tools.py"

# 24 个缺失工具（contract - mycode）
MISSING = [
    "Artifact", "AskUserQuestion", "ClaudeDesign", "EnterPlanMode", "ExitPlanMode",
    "ListMcpResources", "Mcp", "Monitor", "OfferChromeSetup", "Projects",
    "ProposeGoal", "ProposeSkills", "PushNotification", "ReadMcpResource",
    "ReadMcpResourceDir", "ReadNotifications", "RefreshMcpTools", "RemoteTrigger",
    "SendFeedback", "ShowOnboardingRolePicker", "TaskCreate", "TaskGet",
    "TaskList", "TaskUpdate",
]

# 工具级描述（d.ts 无工具级描述，按工具名+参数语义归纳；不确定的标注）
TOOL_DESC = {
    "Artifact": "Create or update an artifact — a file with special rendering (code, markdown, HTML). Use for deliverables the user will view.",
    "AskUserQuestion": "Ask the user one or more multiple-choice questions to gather preferences or clarify an ambiguous request. Each question has 2-4 options.",
    "ClaudeDesign": "Open or manage Claude Design — a visual design surface/canvas for producing UI mockups and designs.",
    "EnterPlanMode": "Enter plan mode: a read-only research phase where you explore the codebase and design an approach without making changes.",
    "ExitPlanMode": "Exit plan mode and present the plan to the user for approval before executing.",
    "ListMcpResources": "List the resources exposed by connected MCP (Model Context Protocol) servers.",
    "Mcp": "Invoke a tool provided by a connected MCP (Model Context Protocol) server.",
    "Monitor": "Monitor a long-running process or condition and get notified when it changes.",
    "OfferChromeSetup": "Offer the user help setting up the Chrome browser extension / browser automation.",
    "Projects": "Manage Projects — organize work into named projects with associated context and files.",
    "ProposeGoal": "Propose a goal for the current session for the user to confirm.",
    "ProposeSkills": "Propose new skills to be created based on the current workflow, for the user to review and adopt.",
    "PushNotification": "Send a push notification to the user (mobile/desktop).",
    "ReadMcpResource": "Read the contents of a specific resource exposed by an MCP server.",
    "ReadMcpResourceDir": "Read a directory listing of resources exposed by an MCP server.",
    "ReadNotifications": "Read pending notifications that were pushed to the user.",
    "RefreshMcpTools": "Refresh the tool list from connected MCP servers (after servers change).",
    "RemoteTrigger": "Trigger an action on a remote agent/session.",
    "SendFeedback": "Send feedback about Claude Code to Anthropic (bug reports, feature requests).",
    "ShowOnboardingRolePicker": "Show the onboarding role picker (first-run experience to select the user's role).",
    "TaskCreate": "Create a new background task in the task list.",
    "TaskGet": "Get the details of a single task by its id.",
    "TaskList": "List all tasks (with their status) in the current task list.",
    "TaskUpdate": "Update an existing task's status, description, or result.",
}


def ts_type_to_schema(ts_type: str) -> dict:
    """把 TS 类型字符串转成（简化的）JSON Schema。"""
    t = " ".join(ts_type.split())
    if not t:
        return {}
    # 纯 string 字面量枚举: "a" | "b" | ...
    literals = re.findall(r'"([^"]*)"', t)
    if literals and "{" not in t and "[" not in t:
        return {"type": "string", "enum": literals}
    if t in ("string",):
        return {"type": "string"}
    if t in ("number", "integer"):
        return {"type": t}
    if t in ("boolean",):
        return {"type": "boolean"}
    if t in ("null",):
        return {"type": "null"}
    # 数组: T[] 或 Array<T>
    if t.endswith("[]"):
        return {"type": "array", "items": ts_type_to_schema(t[:-2])}
    m = re.match(r"Array<(.+)>$", t)
    if m:
        return {"type": "array", "items": ts_type_to_schema(m.group(1))}
    # TS 数组字面量 [ ... ] → array
    if t.startswith("["):
        return {"type": "array", "items": {"type": "object"}}
    # 对象字面量 { ... } → object
    if t.startswith("{") or t.startswith("|"):
        # 联合里含对象 → object；含字面量 → string
        if literals and all(c not in t for c in "{}[]"):
            return {"type": "string", "enum": literals}
        return {"type": "object"}
    # 联合其它
    if "|" in t:
        parts = [p.strip() for p in t.split("|") if p.strip()]
        non_null = [p for p in parts if p != "null"]
        if len(non_null) == 1:
            return ts_type_to_schema(non_null[0])
        return {"type": "object"}
    return {"type": "object"}


def extract_brace_block(text: str, start: int) -> str:
    """从 start（指向 '{'）返回匹配的块内容。"""
    depth = 0
    i = start
    while i < len(text):
        c = text[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[start + 1 : i]
        i += 1
    raise RuntimeError("unbalanced braces")


def parse_interface_fields(body: str) -> dict:
    """健壮解析 TS interface body 的顶层字段（跟踪括号深度，正确处理嵌套类型）。

    对比正则版 [^;]+：本版读到「深度 0 的 ;」才结束，故 questions: | [ {a; b;} ] 不会被截断。
    """
    props: dict = {}
    required: list[str] = []
    i, n = 0, len(body)
    pending_doc = ""
    while i < n:
        if body.startswith("/**", i):
            end = body.find("*/", i)
            if end == -1:
                break
            pending_doc = body[i + 4 : end]
            i = end + 2
            continue
        if body[i].isspace() or body[i] == ",":
            i += 1
            continue
        m = re.match(r'("[^"]+"|[A-Za-z_$][\w$]*)', body[i:])
        if not m:
            i += 1
            continue
        name = m.group(1).strip('"')
        j = i + m.end()
        while j < n and body[j].isspace():
            j += 1
        optional = False
        if j < n and body[j] == "?":
            optional = True
            j += 1
        while j < n and body[j].isspace():
            j += 1
        if j >= n or body[j] != ":":
            i = j + 1
            pending_doc = ""
            continue
        j += 1  # skip ':'
        depth = 0
        start = j
        while j < n:
            c = body[j]
            if c in "{[(":
                depth += 1
            elif c in "}])":
                depth -= 1
            elif c == ";" and depth == 0:
                break
            j += 1
        typ = " ".join(body[start:j].split())
        j += 1  # skip ';'
        desc = ""
        if pending_doc:
            lines = [ln.strip().lstrip("*").strip() for ln in pending_doc.splitlines()]
            lines = [ln for ln in lines if ln]
            desc = lines[0] if lines else ""
        props[name] = {"type": typ, "description": desc}
        if not optional:
            required.append(name)
        pending_doc = ""
        i = j
    return {"properties": props, "required": required}


def build_input_schema(input_contract: dict | None) -> dict:
    """从契约 input 构造 JSON Schema。"""
    if not input_contract:
        return {"type": "object", "properties": {}}
    props_in = input_contract.get("properties", {})
    required = input_contract.get("required", [])
    props: dict = {}
    for name, meta in props_in.items():
        schema = ts_type_to_schema(meta.get("type", ""))
        desc = meta.get("description", "")
        if desc:
            schema["description"] = desc
        props[name] = schema
    out: dict = {"type": "object", "properties": props}
    if required:
        out["required"] = sorted(required)
    return out


def main() -> int:
    data = json.loads(CONTRACTS.read_text(encoding="utf-8"))
    # 从 d.ts 用健壮解析器重解析各工具 interface（修正嵌套类型）
    dts_text = DTS.read_text(encoding="utf-8")
    iface_inputs: dict = {}
    for m in re.finditer(r"export interface (\w+)Input\s*\{", dts_text):
        key = m.group(1)
        brace = dts_text.index("{", m.start())
        iface_inputs[key] = parse_interface_fields(extract_brace_block(dts_text, brace))

    tools_by_name = {}
    for iface, v in data["tools"].items():
        v = dict(v)
        key = iface[:-5] if iface.endswith("Input") else iface
        if key in iface_inputs:
            v["input"] = iface_inputs[key]
        tools_by_name[v["tool_name"]] = v

    lines = [
        '"""Phase 2 自动生成：24 个缺失契约工具（参数/描述对齐 sdk-tools.d.ts）。',
        "",
        "生成脚本: tools/recon/gen_contract_tools.py",
        "不要手改，改脚本后重新生成。",
        '"""',
        "from __future__ import annotations",
        "from typing import Any",
        "",
        "",
        "def _not_implemented(tool_name: str):",
        '    """契约对齐但功能未实现的工具：返回明确的未实现提示（不编造）。"""',
        "    def _run(**kwargs: Any) -> str:",
        '        return f"[{tool_name}] 契约已对齐，但该工具在本环境无对应后端实现（MCP/通知/引导类）。"',
        "    return _run",
        "",
        "",
        "CONTRACT_TOOLS: dict[str, dict] = {",
    ]

    count = 0
    for name in MISSING:
        v = tools_by_name.get(name)
        if v is None:
            print(f"  WARN: 契约中未找到 {name}")
            continue
        schema = build_input_schema(v.get("input"))
        desc = TOOL_DESC.get(name, f"{name} tool.")
        lines.append(f"    {name!r}: {{")
        lines.append(f"        \"name\": {name!r},")
        lines.append(f"        \"description\": {desc!r},")
        lines.append(f"        \"input_schema\": {json.dumps(schema, ensure_ascii=False)},")
        lines.append(f"        \"execute\": _not_implemented({name!r}),")
        lines.append("    },")
        count += 1

    lines.append("}")
    lines.append("")
    lines.append(f"# 共 {count} 个契约工具")
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"生成 {count} 个契约工具 → {OUT}")

    # 断言：所有 MISSING 都在契约里
    missing_not_found = [m for m in MISSING if m not in tools_by_name]
    assert not missing_not_found, f"契约缺失: {missing_not_found}"
    print("Phase 2 断言通过：24 个工具全部从契约生成")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())