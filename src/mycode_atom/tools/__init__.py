"""atomcode 工具集汇总 — 28 个工具（对齐逆向结果）"""
from mycode_atom.tools.basic import BASIC_TOOLS
from mycode_atom.tools.analysis import ANALYSIS_TOOLS
from mycode_atom.tools.advanced import ADVANCED_TOOLS

# 8 基礎 + 9 代码分析 + 11 执行管理/会话/技能 = 28
ALL_TOOLS = {**BASIC_TOOLS, **ANALYSIS_TOOLS, **ADVANCED_TOOLS}
