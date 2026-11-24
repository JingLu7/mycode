"""Agent loop — 核心循环（P1：集成权限、transcript、context management）"""
from __future__ import annotations
import sys
from typing import Any

from mycode.llm.provider import LLMProvider, LLMResponse
from mycode.tools.base import ToolRegistry
from mycode.agent.context import Context
from mycode.agent.transcript import Transcript
from mycode.agent.context_management import estimate_messages_tokens, summarize_old_messages
from mycode.harness.permissions import PermissionManager, PermissionMode
from mycode.harness.hooks import HookManager


class AgentLoop:
    """agent 主循环：prompt → LLM → tool_use → 权限检查 → hooks → 执行 → tool_result → LLM → end"""

    def __init__(
        self,
        llm: LLMProvider,
        tools: ToolRegistry,
        system: str,
        max_iterations: int = 20,
        permission_mode: PermissionMode = PermissionMode.DEFAULT,
        transcript: Transcript | None = None,
        max_context_tokens: int = 30000,
        hooks: HookManager | None = None,
        allow_rules: list[str] | None = None,
        deny_rules: list[str] | None = None,
    ) -> None:
        self.llm = llm
        self.tools = tools
        self.system = system
        self.max_iterations = max_iterations
        self.permissions = PermissionManager(permission_mode, allow_rules, deny_rules)
        self.transcript = transcript
        self.max_context_tokens = max_context_tokens
        self.hooks = hooks or HookManager()

    def run(self, user_prompt: str) -> str:
        """单轮模式：创建新 Context，跑一轮后返回"""
        ctx = Context()
        self.hooks.fire_session_start()
        try:
            return self.run_one_turn(ctx, user_prompt)
        finally:
            self.hooks.fire_session_end()

    def run_one_turn(self, ctx: Context, user_prompt: str) -> str:
        """单轮：追加 prompt 到已有 Context，跑循环，返回输出。

        REPL 与会话恢复复用此方法——外部持有 ctx 跨轮保留消息历史。
        """
        ctx.add_user(user_prompt)
        tool_schemas = self.tools.to_anthropic_schemas()

        self.hooks.fire_user_prompt_submit(user_prompt)

        if self.transcript:
            self.transcript.log_user(user_prompt)

        return self._run_loop(ctx, tool_schemas)

    def _run_loop(self, ctx: Context, tool_schemas: list) -> str:
        for i in range(self.max_iterations):
            # context management：token 超限时摘要旧消息
            messages = ctx.to_list()
            total_tokens = estimate_messages_tokens(messages)
            if total_tokens > self.max_context_tokens:
                self.hooks.fire_pre_compact(total_tokens)
                messages = summarize_old_messages(messages, self.max_context_tokens)
                ctx.messages = messages
                if self.transcript:
                    self.transcript.log({"event": "context_summarized", "tokens_before": total_tokens})

            # 发请求
            response = self.llm.chat(
                messages=messages,
                tools=tool_schemas,
                system=self.system,
            )

            # 输出 thinking（stderr，不干扰 stdout）
            if response.thinking:
                print(f"\n[thinking] {response.thinking}", file=sys.stderr, flush=True)

            # 输出文本内容
            if response.content:
                print(response.content, flush=True)

            # 没有工具调用 → 结束
            if not response.tool_calls:
                if self.transcript:
                    self.transcript.log_assistant(response.content, [])
                self.hooks.fire_stop()
                return response.content

            # 有工具调用 → 权限检查 → 执行 → 回填结果
            tool_use_blocks = []
            for tc in response.tool_calls:
                tool_use_blocks.append({
                    "type": "tool_use",
                    "id": tc.id,
                    "name": tc.name,
                    "input": tc.arguments,
                })

            ctx.add_assistant(response.content, tool_use_blocks, thinking=response.thinking)
            if self.transcript:
                self.transcript.log_assistant(response.content, tool_use_blocks)

            for tc in response.tool_calls:
                print(f"\n[tool] {tc.name}({tc.arguments})", file=sys.stderr, flush=True)

                # hooks: PreToolUse
                pre_result = self.hooks.fire_pre_tool_use(tc.name, tc.arguments)
                if not pre_result.allowed:
                    result = f"[hook blocked] {tc.name}: {pre_result.message}"
                    print(f"[hook blocked] {tc.name}", file=sys.stderr, flush=True)
                else:
                    exec_args = pre_result.modified_args or tc.arguments
                    # 权限检查
                    if not self.permissions.check(tc.name, exec_args):
                        result = f"[permission denied] {tc.name} was not approved by user"
                        print(f"[denied] {tc.name}", file=sys.stderr, flush=True)
                    else:
                        result = self.tools.execute(tc.name, exec_args)
                        # hooks: PostToolUse
                        result = self.hooks.fire_post_tool_use(tc.name, exec_args, result)
                        preview = result[:200] + ("..." if len(result) > 200 else "")
                        print(f"[result] {preview}", file=sys.stderr, flush=True)

                if self.transcript:
                    self.transcript.log_tool_result(tc.name, tc.id, result)
                ctx.add_tool_result(tc.id, result)

        self.hooks.fire_stop()
        return "(max iterations reached)"
