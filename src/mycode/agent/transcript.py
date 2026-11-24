"""会话 transcript — 记录对话到本地文件"""
from __future__ import annotations
import json
import time
from pathlib import Path
from typing import Any


class Transcript:
    """把对话历史追加写入 JSONL 文件"""

    def __init__(self, session_dir: str = "~/.mycode/sessions", session_id: str | None = None) -> None:
        self.session_dir = Path(session_dir).expanduser()
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.session_id = session_id or f"{int(time.time())}"
        self.file_path = self.session_dir / f"{self.session_id}.jsonl"
        self._fp = open(self.file_path, "a", encoding="utf-8")

    def log(self, entry: dict[str, Any]) -> None:
        """写入一条记录"""
        entry["ts"] = time.time()
        self._fp.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
        self._fp.flush()

    def log_user(self, content: str) -> None:
        self.log({"role": "user", "content": content})

    def log_assistant(self, content: str, tool_calls: list[dict] | None = None) -> None:
        self.log({"role": "assistant", "content": content, "tool_calls": tool_calls or []})

    def log_tool_result(self, tool_name: str, tool_id: str, result: str) -> None:
        self.log({"role": "tool_result", "tool_name": tool_name, "tool_id": tool_id, "result": result})

    def latest_session_id(self) -> str | None:
        """找最近的 session 文件 ID（排除当前文件，避免拿到刚创建的空文件）"""
        files = sorted(
            [f for f in self.session_dir.glob("*.jsonl") if f.stem != self.session_id],
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        return files[0].stem if files else None

    @staticmethod
    def load(file_path: str | Path) -> list[dict[str, Any]]:
        """从 JSONL 文件加载消息历史，返回 Anthropic messages 格式（可灌入 Context）"""
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
                    content = entry.get("content", "")
                    tool_calls = entry.get("tool_calls", [])
                    blocks: list[Any] = []
                    if content:
                        blocks.append({"type": "text", "text": content})
                    if tool_calls:
                        blocks.extend(tool_calls)
                    if len(blocks) == 1 and blocks[0].get("type") == "text":
                        messages.append({"role": "assistant", "content": blocks[0]["text"]})
                    else:
                        messages.append({"role": "assistant", "content": blocks})
                elif role == "tool_result":
                    messages.append({
                        "role": "user",
                        "content": [{
                            "type": "tool_result",
                            "tool_use_id": entry["tool_id"],
                            "content": entry["result"],
                        }],
                    })
        return messages

    def close(self) -> None:
        self._fp.close()

    def __del__(self) -> None:
        try:
            self._fp.close()
        except Exception:
            pass