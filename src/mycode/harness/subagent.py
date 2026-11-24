"""Subagent 管理器 — 启动和管理子 agent

subagent 拥有独立的 AgentLoop 实例（独立上下文），
共享 LLM provider 和工具注册表（可按 agent 定义限制工具子集）。
"""
from __future__ import annotations
import uuid
from typing import Any

from mycode.llm.provider import LLMProvider
from mycode.tools.base import ToolRegistry


# 内置 agent 类型定义
_BUILTIN_DEFS: dict[str, dict[str, Any]] = {
    "general": {
        "description": "General-purpose agent for multi-step tasks. Full tool access.",
        "tools": None,  # None = 全部工具
    },
    "explore": {
        "description": "Fast agent for codebase exploration. Read-only tools only.",
        "tools": ["Read", "Glob", "Grep", "WebFetch", "WebSearch"],
    },
    "coder": {
        "description": "Agent for writing and modifying code. File + bash tools.",
        "tools": ["Read", "Write", "Edit", "Glob", "Grep", "Bash"],
    },
}


class SubagentManager:
    """管理 subagent 生命周期（进程内单例）

    支持并行 spawn（ThreadPoolExecutor）+ 子 agent 用 qwen3.5-9b（num_ctx=32768）。
    """

    _instance: "SubagentManager | None" = None

    def __init__(self) -> None:
        self._llm: LLMProvider | None = None
        self._tools: ToolRegistry | None = None
        self._system_prompt: str = ""
        self._max_context_tokens: int = 30000
        self._subagent_model: str = "qwen3.5-9b"
        self._subagent_num_ctx: int = 32768
        self._running: dict[str, dict[str, Any]] = {}
        self._agent_defs: dict[str, dict[str, Any]] = dict(_BUILTIN_DEFS)

    @classmethod
    def instance(cls) -> "SubagentManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def configure(
        self,
        llm: LLMProvider,
        tools: ToolRegistry,
        system_prompt: str,
        max_context_tokens: int = 30000,
        subagent_model: str = "qwen3.5-9b",
        subagent_num_ctx: int = 32768,
    ) -> None:
        """由 CLI 在启动时配置"""
        self._llm = llm
        self._tools = tools
        self._system_prompt = system_prompt
        self._max_context_tokens = max_context_tokens
        self._subagent_model = subagent_model
        self._subagent_num_ctx = subagent_num_ctx

    def register_type(self, name: str, description: str, tools: list[str] | None = None) -> None:
        """注册自定义 agent 类型"""
        self._agent_defs[name] = {"description": description, "tools": tools}

    def list_types(self) -> list[dict[str, Any]]:
        """列出可用 agent 类型"""
        return [{"name": k, "description": v["description"], "tools": v["tools"]} for k, v in self._agent_defs.items()]

    def list_running(self) -> list[dict[str, Any]]:
        """列出运行中的 subagent"""
        return [{"id": k, **v} for k, v in self._running.items()]

    def spawn(self, prompt: str, subagent_type: str = "general", description: str = "") -> str:
        """启动 subagent，返回结果文本"""
        if self._llm is None or self._tools is None:
            return "Error: SubagentManager not configured. Call configure() first."

        agent_def = self._agent_defs.get(subagent_type)
        if agent_def is None:
            available = ", ".join(self._agent_defs.keys())
            return f"Error: unknown agent type '{subagent_type}'. Available: {available}"

        # 构建工具子集
        allowed_tools = agent_def.get("tools")
        if allowed_tools is None:
            sub_tools = self._tools
        else:
            sub_tools = ToolRegistry()
            for name in allowed_tools:
                tool = self._tools.get(name)
                if tool:
                    sub_tools.register(tool)

        # 生成 agent ID
        agent_id = f"agent-{uuid.uuid4().hex[:8]}"
        self._running[agent_id] = {
            "subagent_type": subagent_type,
            "description": description,
            "status": "running",
        }

        try:
            # 延迟导入避免循环依赖
            from mycode.agent.loop import AgentLoop
            from mycode.harness.permissions import PermissionMode
            from mycode.llm.ollama import OllamaProvider

            sub_system = f"[Subagent: {subagent_type}]\n{self._system_prompt}"
            # 子 agent 用 qwen3.5-9b（num_ctx=32768），与主模型并行
            sub_llm = OllamaProvider(
                model=self._subagent_model,
                base_url=getattr(self._llm, 'base_url', 'http://localhost:11434'),
                num_ctx=self._subagent_num_ctx,
                think=True,
            )
            sub_loop = AgentLoop(
                llm=sub_llm,
                tools=sub_tools,
                system=sub_system,
                max_iterations=15,
                permission_mode=PermissionMode.BYPASS,
                transcript=None,
                max_context_tokens=self._max_context_tokens,
            )
            result = sub_loop.run(prompt)
            self._running[agent_id]["status"] = "completed"
            self._running[agent_id]["result"] = result
            return f"[Subagent {agent_id} ({subagent_type}) completed]\n{result}"
        except Exception as e:
            self._running[agent_id]["status"] = "failed"
            self._running[agent_id]["error"] = str(e)
            return f"Error: subagent failed: {type(e).__name__}: {e}"
    def spawn_all(self, tasks: list[tuple[str, str, str]]) -> list[dict[str, str]]:
        """并行启动多个 subagent（ThreadPoolExecutor）。

        参数 tasks: [(prompt, subagent_type, description), ...]
        返回: [{"agent_id": ..., "result": ..., "status": ...}, ...]
        """
        import concurrent.futures

        def _spawn_one(args: tuple[str, str, str]) -> dict[str, str]:
            prompt, subagent_type, description = args
            result = self.spawn(prompt, subagent_type, description)
            # 从 result 中提取 agent_id
            agent_id = "unknown"
            if "[Subagent " in result:
                start = result.index("[Subagent ") + 10
                end = result.index(" ", start)
                agent_id = result[start:end]
            return {"agent_id": agent_id, "result": result, "status": "completed" if "completed" in result else "failed"}

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(tasks)) as executor:
            futures = [executor.submit(_spawn_one, t) for t in tasks]
            return [f.result() for f in concurrent.futures.as_completed(futures)]