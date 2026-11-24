"""Settings — 4 层级配置加载（对齐 claude-code）

层级（低 → 高优先级，后者覆盖前者）：
  managed  系统级：/etc/mycode/settings.json
  user     用户级：~/.mycode/settings.json
  project  项目级：<cwd>/.mycode/settings.json
  local    本地级：<cwd>/.mycode/settings.local.json
"""
from __future__ import annotations
import json
from pathlib import Path

# 合并顺序：从低到高
LAYER_ORDER = ["managed", "user", "project", "local"]


class Settings:
    """4 层级 settings 加载与合并"""

    def __init__(
        self,
        cwd: str,
        home: str | None = None,
        managed_path: str | None = None,
    ) -> None:
        self.cwd = Path(cwd)
        self.home = Path(home) if home else Path.home() / ".mycode"
        self.managed_path = Path(managed_path) if managed_path else Path("/etc/mycode/settings.json")
        self.data: dict = {}
        self.loaded_layers: list[str] = []

    def layer_paths(self) -> dict[str, Path]:
        return {
            "managed": self.managed_path,
            "user": self.home / "settings.json",
            "project": self.cwd / ".mycode" / "settings.json",
            "local": self.cwd / ".mycode" / "settings.local.json",
        }

    def load(self) -> dict:
        """按 LAYER_ORDER 合并各层；记录实际加载的层名。"""
        merged: dict = {}
        loaded: list[str] = []
        for layer in LAYER_ORDER:
            p = self.layer_paths()[layer]
            if not p.is_file():
                continue
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                continue
            if isinstance(data, dict):
                merged.update(data)
                loaded.append(layer)
        self.data = merged
        self.loaded_layers = loaded
        return merged

    def get(self, key: str, default=None):
        if not self.data:
            self.load()
        return self.data.get(key, default)

    # 便捷访问器
    def allow_rules(self) -> list[str]:
        return self.get("permissions", {}).get("allow", []) if isinstance(self.get("permissions"), dict) else []

    def deny_rules(self) -> list[str]:
        return self.get("permissions", {}).get("deny", []) if isinstance(self.get("permissions"), dict) else []

    def hooks(self) -> dict:
        h = self.get("hooks", {})
        return h if isinstance(h, dict) else {}

    def env(self) -> dict:
        e = self.get("env", {})
        return e if isinstance(e, dict) else {}