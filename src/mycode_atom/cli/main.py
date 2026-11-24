"""atomcode CLI 入口 — python -m mycode_atom

启动方式分类：
  python -m mycode       → claude-code 复现（Anthropic 格式）
  python -m mycode_atom  → atomcode 复现（OpenAI 格式）
"""
from __future__ import annotations
import argparse
import os
import sys
import platform as plat


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="mycode_atom",
        description="mycode_atom — atomcode 复现（逆向 atomcode 的 agent loop / harness / 28 tools）",
    )
    parser.add_argument("prompt", nargs="?", help="用户提示词（省略则进 REPL）")
    parser.add_argument("--model", default="qwen3.8-27b", help="ollama 模型名")
    parser.add_argument("--base-url", default="http://localhost:11434", help="ollama 服务地址")
    parser.add_argument("--num-ctx", type=int, default=262144, help="上下文窗口")
    parser.add_argument("--no-think", action="store_true", help="关闭 thinking")
    parser.add_argument("--max-tokens", type=int, default=32768, help="上下文 token 上限")
    parser.add_argument("--continue", dest="continue_session", action="store_true", help="继续最近的会话")
    parser.add_argument("--resume", dest="resume_session", metavar="SESSION_ID", help="恢复指定 session")
    parser.add_argument("--no-transcript", action="store_true", help="不记录会话 transcript")
    args = parser.parse_args()

    from mycode_atom.llm.openai_provider import OpenAIProvider
    from mycode_atom.agent.loop import AgentLoop
    from mycode_atom.agent.context import Context
    from mycode_atom.agent.transcript import Transcript
    from mycode_atom.prompt.system import build_system_prompt
    from mycode_atom.tools import ALL_TOOLS

    cwd = os.getcwd()

    llm = OpenAIProvider(
        model=args.model,
        base_url=args.base_url,
        num_ctx=args.num_ctx,
        think=not args.no_think,
    )

    system = build_system_prompt(cwd=cwd, model=args.model)

    transcript = None if args.no_transcript else Transcript()

    # 会话恢复
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
            transcript.close()
            if transcript.file_path.exists() and transcript.file_path.stat().st_size == 0:
                transcript.file_path.unlink()
            transcript = Transcript(session_id=resume_id)
        else:
            print(f"[会话] 文件不存在: {resume_id}", file=sys.stderr)
            resume_id = None

    loop = AgentLoop(
        llm=llm,
        tools=ALL_TOOLS,
        system=system,
        max_context_tokens=args.max_tokens,
        cwd=cwd,
        transcript=transcript,
    )

    print(f"mycode_atom — atomcode 复现 | model={args.model} | tools={len(ALL_TOOLS)} | cwd={cwd}", file=sys.stderr)

    try:
        if args.prompt:
            if history:
                ctx = Context()
                ctx.messages = history
                loop.run_one_turn(ctx, args.prompt)
            else:
                loop.run(args.prompt)
        else:
            ctx = Context()
            if history:
                ctx.messages = history
            print("mycode_atom REPL — /exit 退出 | /tools 查看工具 | /session 查看会话", file=sys.stderr)
            while True:
                try:
                    prompt = input(">>> ").strip()
                except EOFError:
                    break
                if not prompt:
                    continue
                if prompt in ("/exit", "/quit"):
                    break
                if prompt == "/tools":
                    print(f"  {len(ALL_TOOLS)} tools: {', '.join(ALL_TOOLS.keys())}", file=sys.stderr)
                    continue
                if prompt == "/session":
                    if transcript:
                        sid = transcript.latest_session_id()
                        print(f"  current: {transcript.session_id} | latest: {sid}", file=sys.stderr)
                    continue
                try:
                    loop.run_one_turn(ctx, prompt)
                except KeyboardInterrupt:
                    print("\n[interrupted]", file=sys.stderr)
    finally:
        if transcript:
            transcript.close()


if __name__ == "__main__":
    main()
