# 概念

mycode 的架构形态决策与设计约束。
- [架构形态决策](architecture.md)：贴近 claude-code 原栈 + 对外可复用接口；首版交付 harness 逆向报告。
- [P2 工具完善策略](p2-tool-completion-strategy.md)：22 个工具的设计决策和实现策略。
- [沙箱环境限制](sandbox-network-and-fs-limitations.md)：网络隔离和只读文件系统对测试的影响及应对。
- [ollama 模型能力实测](ollama-model-capabilities.md)：num_ctx 默认拉满 256K、thinking+tool 同时、并行显存占用、多轮消息格式。
