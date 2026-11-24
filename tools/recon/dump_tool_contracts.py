#!/usr/bin/env python3
"""R1: 白盒解析 sdk-tools.d.ts 全量工具契约

产出 artifacts/recon/tool-contracts.json：
- union 成员（工具名）
- 每个工具的 Input 字段（name/type/required/description）
- 每个工具是否有 Output 定义
- 与运行时捕获的 20 工具做差异对比

测试实验：脚本末尾断言所有 union 成员都有 Input 契约。
"""
from __future__ import annotations
import json
import re
from pathlib import Path

DTS = Path("/home/zigaa/.local/lib/node_modules/@anthropic-ai/claude-code/sdk-tools.d.ts")
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "recon" / "tool-contracts.json"
RUNTIME = ROOT / "artifacts" / "recon" / "tools.json"


def extract_union_members(text: str) -> list[str]:
    m = re.search(r"export type ToolInputSchemas =(.*?);", text, re.DOTALL)
    if not m:
        raise RuntimeError("ToolInputSchemas union not found")
    members = re.findall(r"\|\s*([A-Za-z0-9_]+)", m.group(1))
    return [x for x in members if x != "ToolOutputSchemas"]


def extract_brace_block(text: str, start: int) -> str:
    """从 start（指向 '{'）开始，返回匹配的块内容"""
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


def parse_fields(body: str) -> dict:
    """解析 interface body 的字段"""
    props: dict = {}
    required: list[str] = []
    pattern = re.compile(
        r"(?:/\*\*(?P<doc>.*?)\*/)?\s*"
        r'(?P<name>"[^"]+"|[A-Za-z_$][\w$]*)\s*(?P<opt>\?)?:\s*'
        r"(?P<type>[^;]+);",
        re.DOTALL,
    )
    for m in pattern.finditer(body):
        name = m.group("name").strip('"')
        if not name:
            continue
        typ = " ".join(m.group("type").split())
        doc = m.group("doc")
        desc = ""
        if doc:
            lines = [ln.strip().lstrip("*").strip() for ln in doc.splitlines()]
            lines = [ln for ln in lines if ln]
            desc = lines[0] if lines else ""
        props[name] = {"type": typ, "description": desc}
        if not m.group("opt"):
            required.append(name)
    return {"properties": props, "required": required}


def norm(n: str) -> str:
    """归一化工具名：去 Input 后缀；FileRead→Read"""
    n = n[:-5] if n.endswith("Input") else n
    if n.startswith("File") and n[4:] in ("Read", "Edit", "Write"):
        return n[4:]
    return n


def main() -> int:
    text = DTS.read_text(encoding="utf-8")
    members = extract_union_members(text)

    inputs: dict = {}
    for m in re.finditer(r"export interface (\w+)Input\s*\{", text):
        name = m.group(1)
        brace = text.index("{", m.start())
        inputs[name] = parse_fields(extract_brace_block(text, brace))

    outputs = {m.group(1) for m in re.finditer(r"export (?:interface|type) (\w+)Output\b", text)}

    tools = {}
    for member in members:
        file_name = member[:-5] if member.endswith("Input") else member
        tools[member] = {
            "interface": member,
            "tool_name": norm(member),
            "has_input": file_name in inputs,
            "input": inputs.get(file_name),
            "has_output": file_name in outputs,
        }

    runtime: list[str] = []
    if RUNTIME.exists():
        runtime = [t["name"] for t in json.loads(RUNTIME.read_text())]

    contract_names = sorted({norm(m) for m in members})
    contract_set, runtime_set = set(contract_names), set(runtime)

    result = {
        "source": str(DTS),
        "union_member_count": len(members),
        "contract_tool_count": len(contract_names),
        "runtime_captured_count": len(runtime),
        "contract_tools": contract_names,
        "runtime_captured": sorted(runtime_set),
        "in_contract_not_runtime": sorted(contract_set - runtime_set),
        "in_runtime_not_contract": sorted(runtime_set - contract_set),
        "tools": tools,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False))

    print(f"union 成员数: {len(members)}")
    print(f"去重后契约工具数: {len(contract_names)}")
    print(f"运行时捕获: {len(runtime)}")
    print(f"契约有但运行时无: {len(result['in_contract_not_runtime'])}")
    print(f"运行时有但契约无: {len(result['in_runtime_not_contract'])}")
    print(f"解析出 Input 的接口数: {len(inputs)}")
    print(f"产出: {OUT}")

    missing_input = [m for m in members if not tools[m]["has_input"]]
    assert not missing_input, f"以下 union 成员没有 Input interface: {missing_input}"
    print("R1 断言通过：所有 union 成员都有 Input 契约")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())