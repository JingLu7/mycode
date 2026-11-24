"""Plugins — 插件系统（对齐 claude-code）

目录结构：
  ~/.mycode/plugins/
    installed_plugins.json   已安装插件清单
    known_marketplaces.json  已知市场
    cache/                   插件缓存
    marketplaces/            市场数据

settings.json 的 enabledPlugins 字段控制启用/禁用。
"""
from __future__ import annotations
import json
from pathlib import Path


class PluginManager:
    """插件清单加载与启用状态查询"""

    def __init__(self, home: str | None = None) -> None:
        self.home = Path(home) if home else Path.home() / ".mycode"
        self.plugins_dir = self.home / "plugins"
        self.installed_file = self.plugins_dir / "installed_plugins.json"
        self.marketplaces_file = self.plugins_dir / "known_marketplaces.json"

    def _read_json(self, p: Path):
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return None

    def list_installed(self) -> list[dict]:
        """返回已安装插件列表（每条含 scope/installPath/version 等）。"""
        data = self._read_json(self.installed_file)
        if data is None:
            return []
        if isinstance(data, dict):
            plugins = data.get("plugins", [])
            return plugins if isinstance(plugins, list) else []
        return data if isinstance(data, list) else []

    def list_marketplaces(self) -> list[dict]:
        data = self._read_json(self.marketplaces_file)
        if data is None:
            return []
        if isinstance(data, dict):
            mk = data.get("marketplaces", [])
            return mk if isinstance(mk, list) else []
        return data if isinstance(data, list) else []

    def enabled_names(self, settings) -> list[str]:
        """从 settings 的 enabledPlugins 取启用插件名。"""
        ep = settings.get("enabledPlugins", {}) if settings is not None else {}
        if isinstance(ep, dict):
            return [k for k, v in ep.items() if v]
        return []

    def status(self, settings=None) -> dict:
        return {
            "installed": [p.get("name", p.get("scope", "?")) for p in self.list_installed()],
            "enabled": self.enabled_names(settings),
            "marketplaces": [m.get("name", "?") for m in self.list_marketplaces()],
        }