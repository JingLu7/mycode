"""Bash 工具 — 执行 shell 命令"""
from __future__ import annotations
import subprocess


def execute(command: str, timeout: int = 120, description: str = "") -> str:
    """执行 shell 命令并返回 stdout+stderr"""
    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    output = result.stdout
    if result.stderr:
        if output:
            output += f"\nstderr:\n{result.stderr}"
        else:
            output = result.stderr
    if result.returncode != 0:
        output += f"\n(exit code: {result.returncode})"
    return output or "(no output)"


TOOL_SCHEMA = {
    "name": "Bash",
    "description": "Execute a bash shell command and return stdout, stderr, and exit code.",
    "input_schema": {
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "The shell command to execute."},
            "timeout": {"type": "integer", "description": "Timeout in seconds.", "default": 120},
            "description": {"type": "string", "description": "Short description of the command."},
        },
        "required": ["command"],
    },
    "execute": execute,
}
