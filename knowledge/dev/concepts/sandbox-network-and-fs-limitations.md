---
name: sandbox-network-and-fs-limitations
description: 沙箱环境对网络和文件系统的限制及应对策略
type: runbook
created: 2026-10-12
tags: [mycode, sandbox, testing, environment]
---

# 沙箱环境限制

## 网络隔离
沙箱无外部网络访问（DNS 解析失败）。
- WebFetch/WebSearch 无法在沙箱内做真实网络测试
- 测试策略：验证非网络逻辑（URL 解析、HTML 转换、域名过滤、localhost 拒绝）
- 真实网络测试需在非隔离环境运行

## 只读文件系统
`/home/zigaa/.mycode/` 是只读文件系统。
- Skill 文件加载（~/.mycode/skills/*.md）无法在沙箱内测试
- Cron 持久化（~/.mycode/scheduled_tasks.json）无法写入
- 测试策略：用 tempfile.mkdtemp() 创建临时目录测试文件加载逻辑

## 应对模式
1. 区分"逻辑测试"和"环境测试"——逻辑测试在沙箱内完成
2. 用 mock/临时目录替代真实环境
3. 在 knowledge 中记录限制，避免未来重复踩坑