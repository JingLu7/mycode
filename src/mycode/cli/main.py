"""CLI 入口（P1：6 工具 + 权限 + transcript + context management）"""
from __future__ import annotations
import argparse
import os
import sys
import platform as plat


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="mycode",
        description="mycode — 本地 AI 编程助手",
    )
    parser.add_argument("prompt", nargs="?", help="用户提示词")
    parser.add_argument("--model", default="qwen3.8-27b", help="ollama 模型名（默认主模型 qwen3.8-27b）")
    parser.add_argument("--base-url", default="http://localhost:11434", help="ollama 服务地址")
    parser.add_argument("--num-ctx", type=int, default=262144, help="上下文窗口 num_ctx（默认 256K，按角色分配）")
    parser.add_argument("--no-think", action="store_true", help="关闭 thinking（qwen3-coder 等不支持 thinking 的模型用）")
    parser.add_argument(
        "--permission-mode",
        choices=["default", "acceptEdits", "plan", "bypassPermissions"],
        default="default",
        help="权限模式（对齐 claude-code 4 模式）：default / acceptEdits / plan / bypassPermissions",
    )
    parser.add_argument("--no-transcript", action="store_true", help="不记录会话 transcript")
    parser.add_argument("--continue", dest="continue_session", action="store_true", help="继续最近的会话")
    parser.add_argument("--resume", dest="resume_session", metavar="SESSION_ID", help="恢复指定 session")
    parser.add_argument("--max-tokens", type=int, default=30000, help="上下文 token 上限")
    args = parser.parse_args()


    # 延迟导入
    from mycode.llm.ollama import OllamaProvider
    from mycode.tools.base import Tool, ToolRegistry
    from mycode.tools.bash import TOOL_SCHEMA as bash_schema
    from mycode.tools.read import TOOL_SCHEMA as read_schema
    from mycode.tools.write import TOOL_SCHEMA as write_schema
    from mycode.tools.edit import TOOL_SCHEMA as edit_schema
    from mycode.tools.glob import TOOL_SCHEMA as glob_schema
    from mycode.tools.grep import TOOL_SCHEMA as grep_schema
    from mycode.tools.webfetch import TOOL_SCHEMA as webfetch_schema
    from mycode.tools.websearch import TOOL_SCHEMA as websearch_schema
    from mycode.tools.notebook_edit import TOOL_SCHEMA as notebook_edit_schema
    from mycode.tools.task_stop import TOOL_SCHEMA as task_stop_schema
    from mycode.tools.agent import TOOL_SCHEMA as agent_schema
    from mycode.tools.list_agents import TOOL_SCHEMA as list_agents_schema
    from mycode.tools.skill import TOOL_SCHEMA as skill_schema
    from mycode.tools.cron import CRON_CREATE_SCHEMA, CRON_DELETE_SCHEMA, CRON_LIST_SCHEMA
    from mycode.tools.worktree import ENTER_WORKTREE_SCHEMA, EXIT_WORKTREE_SCHEMA
    from mycode.tools.messaging import SEND_MESSAGE_SCHEMA, REPORT_FINDINGS_SCHEMA, SCHEDULE_WAKEUP_SCHEMA
    from mycode.tools.workflow import TOOL_SCHEMA as workflow_schema
    from mycode.tools.todo_write import TOOL_SCHEMA as todo_write_schema
    from mycode.tools.contract_tools import CONTRACT_TOOLS
    from mycode.prompt.system import build_system_prompt
    from mycode.agent.loop import AgentLoop
    from mycode.agent.transcript import Transcript
    from mycode.agent.context import Context
    from mycode.harness.permissions import PermissionMode
    from mycode.harness.subagent import SubagentManager

    # 组装工具注册表（22 工具）
    registry = ToolRegistry()
    for schema in (
        bash_schema, read_schema, write_schema, edit_schema,
        glob_schema, grep_schema, webfetch_schema, websearch_schema,
        notebook_edit_schema, task_stop_schema,
        agent_schema, list_agents_schema, skill_schema,
        CRON_CREATE_SCHEMA, CRON_DELETE_SCHEMA, CRON_LIST_SCHEMA,
        ENTER_WORKTREE_SCHEMA, EXIT_WORKTREE_SCHEMA,
        SEND_MESSAGE_SCHEMA, REPORT_FINDINGS_SCHEMA, SCHEDULE_WAKEUP_SCHEMA,
        workflow_schema, todo_write_schema,
    ):
        registry.register(Tool(
            name=schema["name"],
            description=schema["description"],
            input_schema=schema["input_schema"],
            execute=schema["execute"],
        ))

    # 注册 24 个契约工具（Phase 2：44 工具全量对齐 sdk-tools.d.ts）
    for _spec in CONTRACT_TOOLS.values():
        registry.register(Tool(
            name=_spec["name"],
            description=_spec["description"],
            input_schema=_spec["input_schema"],
            execute=_spec["execute"],
        ))

    # 组装 LLM provider
    llm = OllamaProvider(
        model=args.model,
        base_url=args.base_url,
        num_ctx=args.num_ctx,
        think=not args.no_think,
    )

    # 组装 system prompt
    from mycode.harness.memory import MemoryManager

    mem = MemoryManager(cwd=os.getcwd())
    memory_dir = str(mem.auto_memory_dir())
    system = build_system_prompt(
        cwd=os.getcwd(),
        platform=plat.system().lower(),
        memory_section=mem.to_prompt_section(),
        memory_dir=memory_dir,
    )

    # 配置 SubagentManager（子 agent 用 qwen3.5-9b，num_ctx=32768，与主模型并行）
    SubagentManager.instance().configure(
        llm=llm,
        tools=registry,
        system_prompt=system,
        max_context_tokens=args.max_tokens,
        subagent_model="qwen3.5-9b",
        subagent_num_ctx=32768,
    )

    # 组装 transcript
    transcript = None if args.no_transcript else Transcript()

    # 组装权限模式（4 层级 settings 的 allow/deny 规则并入）
    from mycode.harness.settings import Settings

    settings = Settings(cwd=os.getcwd())
    settings.load()
    perm_mode = PermissionMode(args.permission_mode)

    # 运行 agent loop
    loop = AgentLoop(
        llm=llm,
        tools=registry,
        system=system,
        permission_mode=perm_mode,
        transcript=transcript,
        max_context_tokens=args.max_tokens,
        allow_rules=settings.allow_rules(),
        deny_rules=settings.deny_rules(),
    )

    # 会话恢复：加载历史消息
    history: list = []
    resume_id = args.resume_session
    if not resume_id and args.continue_session and transcript:
        resume_id = transcript.latest_session_id()
        if not resume_id:
            print("[会话] 没有找到历史会话", file=sys.stderr)

    if resume_id and transcript:
        session_file = transcript.session_dir / f"{resume_id}.jsonl"
        if session_file.exists():
            history = Transcript.load(session_file)
            print(f"[会话] 恢复 {resume_id}（{len(history)} 条消息）", file=sys.stderr)
            # 复用已有 session 继续写
            transcript.close()
            # 清理刚创建的空文件（避免遗留孤儿文件）
            if transcript.file_path.exists() and transcript.file_path.stat().st_size == 0:
                transcript.file_path.unlink()
            transcript = Transcript(session_id=resume_id)
            loop.transcript = transcript
        else:
            print(f"[会话] 文件不存在: {resume_id}", file=sys.stderr)
            resume_id = None

    try:
        if args.prompt:
            # 有 prompt：单轮模式（可能带历史）
            if history:
                ctx = Context()
                ctx.messages = history
                loop.hooks.fire_session_start()
                try:
                    loop.run_one_turn(ctx, args.prompt)
                finally:
                    loop.hooks.fire_session_end()
            else:
                loop.run(args.prompt)
        else:
            # 无 prompt：REPL 交互模式
            ctx = Context()
            if history:
                ctx.messages = history
            loop.hooks.fire_session_start()
            print("mycode REPL — 输入 /exit 或 Ctrl+D 退出", file=sys.stderr)
            try:
                while True:
                    try:
                        prompt = input(">>> ").strip()
                    except EOFError:
                        break
                    if not prompt:
                        continue
                    if prompt in ("/exit", "/quit"):
                        break
                    try:
                        loop.run_one_turn(ctx, prompt)
                    except KeyboardInterrupt:
                        print("\n[interrupted]", file=sys.stderr)
            finally:
                loop.hooks.fire_session_end()
    finally:
        if transcript:
            transcript.close()


if __name__ == "__main__":
    main()
