"""atomcode agent loop — 逆向 atomcode 的 agent 循环

核心差异（vs claude-code 复现）：
- OpenAI 格式 tool_calls/tool_result（非 Anthropic content blocks）
- system prompt 22 段（非 11 段）
- 28 个工具（含 AST/符号/调用图等代码分析工具）
- 工作目录沙箱（文件访问限制在 cwd 内）
"""
from __future__ import annotations
import sys
import json
import time
from typing import Any

from mycode_atom.llm.openai_provider import OpenAIProvider
from mycode_atom.agent.context import Context
from mycode_atom.agent.transcript import Transcript


class AgentLoop:
    """atomcode agent 主循环：prompt → LLM → tool_calls → 执行 → tool_result → LLM → end"""

    def __init__(
        self,
        llm: OpenAIProvider,
        tools: dict[str, dict[str, Any]],
        system: str,
        max_iterations: int = 30,
        max_context_tokens: int = 32768,
        cwd: str = ".",
        transcript: Transcript | None = None,
    ) -> None:
        self.llm = llm
        self.tools = tools
        self.system = system
        self.max_iterations = max_iterations
        self.max_context_tokens = max_context_tokens
        self.cwd = cwd
        self.transcript = transcript
        self.cwd = cwd

    def run(self, user_prompt: str) -> str:
        """单轮模式"""
        ctx = Context()
        return self.run_one_turn(ctx, user_prompt)

    def run_one_turn(self, ctx: Context, user_prompt: str) -> str:
        """单轮：追加 prompt 到已有 Context，跑循环（REPL/会话恢复复用）"""
        ctx.add_user(user_prompt)
        if self.transcript:
            self.transcript.log_user(user_prompt)
        # atomcode 的 system-reminder：注入日期
        from datetime import date
        weekday = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][date.today().weekday()]
        ctx.add_user(f"<system-reminder>\nCurrent date: {date.today().isoformat()} ({weekday})\n</system-reminder>")
        return self._run_loop(ctx)

    def _run_loop(self, ctx: Context) -> str:
        tool_schemas = self._build_tool_schemas()

        for i in range(self.max_iterations):
            messages = ctx.to_list()

            # 发请求
            response = self.llm.chat(messages=messages, tools=tool_schemas, system=self.system)

            # 输出 thinking（stderr）
            if response.thinking:
                print(f"\n[thinking] {response.thinking}", file=sys.stderr, flush=True)

            # 输出文本内容
            if response.content:
                print(response.content, flush=True)

            # 没有工具调用 → 结束
            if not response.tool_calls:
                ctx.add_assistant(response.content, None, thinking=response.thinking)
                if self.transcript:
                    self.transcript.log_assistant(response.content, None)
                return response.content

            # 有工具调用 → 执行 → 回填结果（OpenAI 格式）
            tool_calls_oi = []
            for tc in response.tool_calls:
                tool_calls_oi.append({
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.name,
                        "arguments": json.dumps(tc.arguments, ensure_ascii=False),
                    },
                })

            ctx.add_assistant(response.content, tool_calls_oi, thinking=response.thinking)
            if self.transcript:
                self.transcript.log_assistant(response.content, tool_calls_oi)

            for tc in response.tool_calls:
                print(f"\n[tool] {tc.name}({tc.arguments})", file=sys.stderr, flush=True)

                # 执行工具
                result = self._execute_tool(tc.name, tc.arguments)

                preview = result[:200] + ("..." if len(result) > 200 else "")
                print(f"[result] {preview}", file=sys.stderr, flush=True)

                ctx.add_tool_result(tc.id, result)
                if self.transcript:
                    self.transcript.log_tool_result(tc.id, result)

        return "(max iterations reached)"

    def _build_tool_schemas(self) -> list[dict]:
        """构建 OpenAI 格式的工具定义"""
        schemas = []
        for name, spec in self.tools.items():
            schemas.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": spec.get("description", ""),
                    "parameters": spec.get("parameters", {}),
                },
            })
        return schemas

    def _execute_tool(self, name: str, args: dict) -> str:
        """执行工具，返回结果字符串"""
        if name not in self.tools:
            return f"Unknown tool: {name}"
        execute = self.tools[name].get("execute")
        if not execute:
            return f"Tool {name} has no execute function"
        try:
            return execute(args, cwd=self.cwd)
        except Exception as e:
            return f"Error: {e}"