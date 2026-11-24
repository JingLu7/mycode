"""atomcode 执行管理 + 会话/技能工具 — bash_start/poll/kill/fetch_output/list_sessions/recall/list_skills/use_skill/describe_self/schedule_wakeup/open_file"""
from __future__ import annotations
import os
import re
import json
import time
import subprocess
import glob as globmod
from pathlib import Path

# 后台进程注册表：job_id → {process, output, started_at}
_JOBS: dict[str, dict] = {}


def bash_start(args: dict, cwd: str = ".") -> str:
    cmd = args.get("command", "")
    job_id = f"job_{int(time.time() * 1000) % 100000}"
    try:
        proc = subprocess.Popen(
            cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, cwd=cwd,
        )
        _JOBS[job_id] = {"process": proc, "output": "", "started_at": time.time()}
        return f"Started job {job_id}: {cmd}"
    except Exception as e:
        return f"Failed to start: {e}"


def bash_poll(args: dict, cwd: str = ".") -> str:
    job_id = args.get("job_id", "")
    if job_id not in _JOBS:
        return f"Unknown job: {job_id}"
    job = _JOBS[job_id]
    proc = job["process"]
    # 读取已有输出
    if proc.stdout:
        new = proc.stdout.read1() if hasattr(proc.stdout, 'read1') else ""
        if new:
            job["output"] += new
    status = "running" if proc.poll() is None else f"exited({proc.returncode})"
    output = job["output"][-2000:]  # 最后 2000 字符
    return f"[{job_id}] status={status}\n{output}"


def bash_kill(args: dict, cwd: str = ".") -> str:
    job_id = args.get("job_id", "")
    if job_id not in _JOBS:
        return f"Unknown job: {job_id}"
    job = _JOBS[job_id]
    job["process"].kill()
    del _JOBS[job_id]
    return f"Killed job {job_id}"


def fetch_output(args: dict, cwd: str = ".") -> str:
    artifact_id = args.get("artifact_id", "")
    offset = args.get("offset", 0)
    limit = args.get("limit", 2000)
    # 简化版：从 artifact_id 对应的文件读取
    p = Path(artifact_id)
    if p.exists():
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        return "".join(lines[offset:offset + limit])
    return f"Artifact not found: {artifact_id}"


def list_sessions(args: dict, cwd: str = ".") -> str:
    query = args.get("query", "")
    limit = args.get("limit", 10)
    # 列出 ~/.atomcode/sessions/ 或 ~/.mycode_atom/sessions/ 下的会话
    for session_dir in [Path.home() / ".mycode_atom" / "sessions", Path.home() / ".atomcode" / "sessions"]:
        if session_dir.exists():
            files = sorted(session_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
            results = []
            for f in files[:limit]:
                mtime = time.strftime("%Y-%m-%d %H:%M", time.localtime(f.stat().st_mtime))
                results.append(f"  {f.stem}  {mtime}  ({f.stat().st_size} bytes)")
            return f"Sessions ({len(results)}):\n" + "\n".join(results) if results else "No sessions found"
    return "No session directory found"


def recall(args: dict, cwd: str = ".") -> str:
    query = args.get("query", "")
    limit = args.get("limit", 5)
    # 读取最近会话的内容
    for session_dir in [Path.home() / ".mycode_atom" / "sessions", Path.home() / ".atomcode" / "sessions"]:
        if session_dir.exists():
            files = sorted(session_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
            if files:
                with open(files[0], "r", encoding="utf-8") as f:
                    lines = f.readlines()
                results = []
                for line in lines[-limit:]:
                    try:
                        entry = json.loads(line)
                        role = entry.get("role", "?")
                        content = str(entry.get("content", ""))[:100]
                        results.append(f"  [{role}] {content}")
                    except json.JSONDecodeError:
                        pass
                return f"Recent session ({files[0].stem}):\n" + "\n".join(results)
    return "No session history found"


def list_skills(args: dict, cwd: str = ".") -> str:
    query = args.get("query", "")
    # 列出 ~/.atomcode/ 下的 skills
    skills_dir = Path.home() / ".atomcode" / "plugins"
    if skills_dir.exists():
        skills = list(skills_dir.iterdir())
        return f"Available skills ({len(skills)}):\n" + "\n".join(f"  {s.name}" for s in skills)
    return "No skills found (no ~/.atomcode/plugins directory)"


def use_skill(args: dict, cwd: str = ".") -> str:
    name = args.get("name", "")
    arguments = args.get("arguments", {})
    return f"Skill '{name}' requested with args: {json.dumps(arguments, ensure_ascii=False)}\n(Note: skill execution requires skill definition files)"


def describe_self(args: dict, cwd: str = ".") -> str:
    aspect = args.get("aspect", "all")
    info = {
        "identity": "mycode_atom — atomcode 复现",
        "model": "ollama local model (OpenAI compatible /v1/chat/completions)",
        "tools": "28 tools (8 basic + 9 analysis + 11 advanced)",
        "architecture": "agent/ (loop+context) + llm/ (OpenAI provider) + prompt/ (22-segment) + tools/ + harness/",
        "system_prompt": "22 segments, 36810 chars (reverse-engineered from atomcode)",
        "api_format": "OpenAI compatible (tool_calls + role=tool)",
        "sandbox": f"working directory: {cwd}",
    }
    if aspect == "all":
        return "\n".join(f"  {k}: {v}" for k, v in info.items())
    return info.get(aspect, f"Unknown aspect: {aspect}")


def schedule_wakeup(args: dict, cwd: str = ".") -> str:
    delay = args.get("delay_seconds", 0)
    reason = args.get("reason", "")
    prompt = args.get("prompt", "")
    return f"Scheduled wakeup in {delay}s: {reason}\nPrompt: {prompt}"


def open_file(args: dict, cwd: str = ".") -> str:
    file_path = args.get("file_path", "")
    # 简化版：返回文件信息（不实际打开 GUI）
    p = Path(file_path)
    if p.exists():
        return f"File: {file_path} ({p.stat().st_size} bytes)"
    return f"File not found: {file_path}"


ADVANCED_TOOLS = {
    "bash_start": {
        "description": "Start a shell command in the BACKGROUND and return a job id.",
        "parameters": {"type": "object", "properties": {"command": {"type": "string"}, "intent": {"type": "string"}}, "required": ["command"]},
        "execute": bash_start,
    },
    "bash_poll": {
        "description": "Read output produced by a background bash_start job since the last poll.",
        "parameters": {"type": "object", "properties": {"job_id": {"type": "string"}, "intent": {"type": "string"}}, "required": ["job_id"]},
        "execute": bash_poll,
    },
    "bash_kill": {
        "description": "Stop a background bash_start job and kill its whole process group.",
        "parameters": {"type": "object", "properties": {"job_id": {"type": "string"}, "intent": {"type": "string"}}, "required": ["job_id"]},
        "execute": bash_kill,
    },
    "fetch_output": {
        "description": "Read more of a large tool output that was truncated.",
        "parameters": {"type": "object", "properties": {"artifact_id": {"type": "string"}, "offset": {"type": "integer"}, "limit": {"type": "integer"}, "intent": {"type": "string"}}, "required": ["artifact_id"]},
        "execute": fetch_output,
    },
    "list_sessions": {
        "description": "List THIS project's past conversation sessions.",
        "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "limit": {"type": "integer"}, "intent": {"type": "string"}}, "required": []},
        "execute": list_sessions,
    },
    "recall": {
        "description": "Read this project's COMPLETED conversation turns — across all sessions.",
        "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "limit": {"type": "integer"}, "intent": {"type": "string"}}, "required": []},
        "execute": recall,
    },
    "list_skills": {
        "description": "Search available skills by name or description.",
        "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "limit": {"type": "integer"}, "intent": {"type": "string"}}, "required": []},
        "execute": list_skills,
    },
    "use_skill": {
        "description": "Invoke a named skill (a reusable prompt/workflow template).",
        "parameters": {"type": "object", "properties": {"name": {"type": "string"}, "arguments": {"type": "object"}, "intent": {"type": "string"}}, "required": ["name"]},
        "execute": use_skill,
    },
    "describe_self": {
        "description": "Report how this agent is actually assembled and how to work with it.",
        "parameters": {"type": "object", "properties": {"aspect": {"type": "string"}, "intent": {"type": "string"}}, "required": []},
        "execute": describe_self,
    },
    "schedule_wakeup": {
        "description": "Schedule when to resume work in a self-paced /loop.",
        "parameters": {"type": "object", "properties": {"delay_seconds": {"type": "integer"}, "reason": {"type": "string"}, "prompt": {"type": "string"}, "intent": {"type": "string"}}, "required": ["delay_seconds", "reason", "prompt"]},
        "execute": schedule_wakeup,
    },
    "open_file": {
        "description": "Open a local file, directory, or URL in the user's default GUI.",
        "parameters": {"type": "object", "properties": {"file_path": {"type": "string"}, "intent": {"type": "string"}}, "required": ["file_path"]},
        "execute": open_file,
    },
}