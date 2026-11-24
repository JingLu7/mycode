"""Memory 管理 — 3 层记忆（对齐 claude-code）

层 1 全局：~/.mycode/CLAUDE.md
层 2 项目级：<cwd>/AGENTS.md（优先）或 <cwd>/CLAUDE.md
层 3 auto-memory：~/.mycode/memory/MEMORY.md（索引）+ 单条记忆文件

加载后由 prompt/system.py 注入 system prompt 的 # Memory 段。
"""
from __future__ import annotations
from pathlib import Path


class MemoryManager:
    """3 层记忆加载器"""

    def __init__(self, cwd: str, home: str | None = None) -> None:
        self.cwd = Path(cwd)
        self.home = Path(home) if home else Path.home() / ".mycode"

    # ── 层路径 ──
    def global_path(self) -> Path:
        return self.home / "CLAUDE.md"

    def project_paths(self) -> list[Path]:
        return [self.cwd / "AGENTS.md", self.cwd / "CLAUDE.md"]

    def auto_memory_dir(self) -> Path:
        return self.home / "memory"

    def auto_memory_index(self) -> Path:
        return self.auto_memory_dir() / "MEMORY.md"

    # ── 加载 ──
    @staticmethod
    def _read(p: Path) -> str:
        try:
            return p.read_text(encoding="utf-8", errors="replace").strip()
        except Exception:
            return ""

    def load_layers(self) -> dict[str, str]:
        """返回 {层名: 内容}，缺省层不出现。"""
        layers: dict[str, str] = {}
        g = self._read(self.global_path())
        if g:
            layers["global"] = g
        for p in self.project_paths():
            t = self._read(p)
            if t:
                layers[f"project:{p.name}"] = t
                break
        idx = self._read(self.auto_memory_index())
        if idx:
            layers["auto_memory_index"] = idx
        return layers

    def to_prompt_section(self) -> str:
        """生成 # Memory 段（无记忆时返回空串）。"""
        layers = self.load_layers()
        if not layers:
            return ""
        lines = ["# Memory"]
        if "global" in layers:
            lines.append("\n## Global (~/.mycode/CLAUDE.md)\n" + layers["global"])
        for k, v in layers.items():
            if k.startswith("project:"):
                lines.append(f"\n## Project ({k.split(':', 1)[1]})\n" + v)
        if "auto_memory_index" in layers:
            lines.append(
                f"\n## Auto-memory index ({self.auto_memory_dir()})\n"
                + layers["auto_memory_index"]
                + f"\n\nWrite new memories as files under `{self.auto_memory_dir()}`."
            )
        return "\n".join(lines) + "\n"

    def list_layers(self) -> list[str]:
        return list(self.load_layers().keys())