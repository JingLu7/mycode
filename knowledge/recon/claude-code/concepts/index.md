# 概念

claude-code 的稳定结构知识：harness 本质、agent loop 消息协议、system prompt 分段设计。
- [harness 物理结构](harness_structure.md)：Bun ELF 单文件，JSC bytecode 内嵌，字符串明文可提取。
- [agent loop 消息协议](agent_loop_protocol.md)：5 条 messages 结构，mid-conversation system turns，每轮 token 预算注入。
- [system prompt 分段结构](system_prompt_structure.md)：约 5770 字符，11 段（Harness/Memory/Context management 等）。
