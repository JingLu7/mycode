# 接口

claude-code 发往 Anthropic API 的请求参数、beta headers 和工具 schema。
- [请求参数](request_parameters.md)：model、max_tokens、thinking、context_management、output_config、safeguards 等。
- [beta headers](beta_headers.md)：11 个 beta 特性开关（interleaved-thinking、context-management、effort 等）。
- [工具目录](tool_catalog.md)：非交互模式 20 个工具，与 sdk-tools.d.ts 43 个的交叉验证。
- [工具契约解析](tool_contracts_parsing.md)：从 d.ts `ToolInputSchemas` union 解析全量 44 契约的方法与差异表。
- [Agent Loop 协议](agent_loop_protocol.md)：messages 累积、thinking 保留、tool_result 顺序、is_error、cache_control、轮次标记。
- [交互/计划工具](interactive_plan_tools.md)：AskUserQuestion、PlanMode、Task*、ProposeGoal、ReportFindings 契约与模式相关注册规则。
- [运行时机制](runtime_mechanisms.md)：hooks（9 种事件）、permission（模式+规则）、memory（CLAUDE.md+auto-memory）、context management、skills、settings 层级、plugins。
