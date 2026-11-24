"""atomcode 会话 transcript — OpenAI 格式持久化"""
from __future__ import annotations
import json
import time
from pathlib import Path
from typing import Any


class Transcript:
    """把对话历史追加写入 JSONL 文件（OpenAI messages 格式）"""

    def __init__(self, session_dir: str = "~/.mycode_atom/sessions", session_id: str | None = None) -> None:
        self.session_dir = Path(session_dir).expanduser()
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.session_id = session_id or f"{int(time.time())}"
        self.file_path = self.session_dir / f"{self.session_id}.jsonl"
        self._fp = open(self.file_path, "a", encoding="utf-8")

    def log(self, entry: dict[str, Any]) -> None:
        entry["ts"] = time.time()
        self._fp.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
        self._fp.flush()

    def log_user(self, content: str) -> None:
        self.log({"role": "user", "content": content})

    def log_assistant(self, content: str, tool_calls: list[dict] | None = None) -> None:
        self.log({"role": "assistant", "content": content, "tool_calls": tool_calls or []})

    def log_tool_result(self, tool_call_id: str, result: str) -> None:
        self.log({"role": "tool", "tool_call_id": tool_call_id, "content": result})

    def latest_session_id(self) -> str | None:
        files = sorted(
            [f for f in self.session_dir.glob("*.jsonl") if f.stem != self.session_id],
            key=lambda p: p.stat().st_mtime, reverse=True,
        )
        return files[0].stem if files else None

    @staticmethod
    def load(file_path: str | Path) -> list[dict[str, Any]]:
        """从 JSONL 加载消息历史（OpenAI messages 格式，可直接灌入 Context）"""
        messages: list[dict[str, Any]] = []
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                entry = json.loads(line)
                role = entry.get("role")
                if role == "user":
                    messages.append({"role": "user", "content": entry["content"]})
                elif role == "assistant":
                    msg: dict[str, Any] = {"role": "assistant", "content": entry.get("content", "")}
                    if entry.get("tool_calls"):
                        msg["tool_calls"] = entry["tool_calls"]
                    messages.append(msg)
                elif role == "tool":
                    messages.append({"role": "tool", "tool_call_id": entry.get("tool_call_id", ""), "content": entry.get("content", "")})
        return messages

    def close(self) -> None:
        self._fp.close()