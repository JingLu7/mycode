# 通用操作手册

跨目标的踩坑处置与工具链操作步骤。每张卡记录触发条件、症状、根因、处置和验证方式。
- [mock 端点抓取 API 请求](mock_endpoint_capture.md)：用 ANTHROPIC_BASE_URL 把 CLI 出口指向 mock，捕获完整请求体。
- [SSE 流式响应要求](sse_stream_requirement.md)：CLI 发 stream:true，mock 必须返回 text/event-stream，否则 tool_use 被丢弃。
- [沙箱进程清理](sandbox_process_cleanup.md)：沙箱清理跨命令后台进程，须同命令内起 server 与跑 CLI。
- [环境变量控制内容量](env_var_content_control.md)：CLAUDE_CODE_SIMPLE=1 精简 system prompt 和工具列表，逆向时须关掉。
- [ollama thinking 与 tool calling 冲突](ollama_thinking_tool_call.md)：qwen3-32b 必须设 think:false 才返回 tool_calls。
