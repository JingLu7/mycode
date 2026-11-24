# Claude Code 逆向

`@anthropic-ai/claude-code@2.1.296` 的逆向发现。目标版本为 Bun `--compile` 产出的原生 ELF 单文件（246MB），应用 JS 以 JSC bytecode 内嵌，字符串常量明文。

- [概念](concepts/index.md)：harness 结构、agent loop 协议、system prompt 分段。
- [接口](apis/index.md)：请求参数、beta headers、工具目录。
- [操作手册](runbooks/index.md)：抓取 API 请求、驱动 agent loop 的具体步骤。