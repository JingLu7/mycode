"""Phase 3 测试实验 — Harness 全量对齐（3a Hooks + 3b Permission）

验证项：
  3a: Hooks 9 种事件类型 + 对应 fire 方法
  3b: Permission 4 模式 + allow/deny 规则 + 权限规劝（deny 优先）
"""
import sys

sys.path.insert(0, "/data/taoming/project/mycode/src")
from mycode.harness.hooks import HookType, HookManager
from mycode.harness.permissions import PermissionMode, PermissionManager

PASS = 0
FAIL = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS  {name}")
    else:
        FAIL += 1
        print(f"  FAIL  {name}  {detail}")


print("=== Phase 3 测试实验：Harness（Hooks + Permission）===\n")

# ── 3a Hooks 9 种 ──
print("[3a] Hooks 9 种事件类型")
expected_types = {
    "PRE_TOOL_USE", "POST_TOOL_USE", "NOTIFICATION", "STOP", "SUBAGENT_STOP",
    "PRE_COMPACT", "SESSION_START", "SESSION_END", "USER_PROMPT_SUBMIT",
}
actual_types = {m.name for m in HookType}
check("9 种事件齐全", expected_types == actual_types, f"got {actual_types}")

hm = HookManager()
for meth in ["fire_pre_tool_use", "fire_post_tool_use", "fire_notification",
             "fire_stop", "fire_subagent_stop", "fire_pre_compact",
             "fire_session_start", "fire_session_end", "fire_user_prompt_submit"]:
    check(f"{meth} 存在", hasattr(hm, meth))

# 触发一个 session hook 验证可用
fired = []
hm.register_callable(HookType.SESSION_START, lambda ctx: fired.append("start"))
hm.register_callable(HookType.USER_PROMPT_SUBMIT, lambda ctx: fired.append("prompt"))
hm.register_callable(HookType.PRE_COMPACT, lambda ctx: fired.append("compact"))
hm.fire_session_start()
hm.fire_user_prompt_submit("hi")
hm.fire_pre_compact(99999)
check("新 hook 可触发", fired == ["start", "prompt", "compact"], str(fired))

# ── 3b Permission 4 模式 ──
print("\n[3b] Permission 4 模式")
expected_modes = {"default", "acceptEdits", "plan", "bypassPermissions"}
actual_modes = {m.value for m in PermissionMode}
check("4 种模式齐全", expected_modes == actual_modes, f"got {actual_modes}")

# default：read 通过
pm_default = PermissionManager(PermissionMode.DEFAULT)
check("default: Read 通过", pm_default.check("Read", {}) is True)
check("default: Grep 通过", pm_default.check("Grep", {}) is True)

# plan：只读，write 拒绝
pm_plan = PermissionManager(PermissionMode.PLAN)
check("plan: Read 通过", pm_plan.check("Read", {}) is True)
check("plan: Write 拒绝", pm_plan.check("Write", {}) is False)
check("plan: Edit 拒绝", pm_plan.check("Edit", {}) is False)
check("plan: Bash 拒绝", pm_plan.check("Bash", {}) is False)

# bypass：全部通过
pm_bypass = PermissionManager(PermissionMode.BYPASS)
check("bypass: Bash 通过", pm_bypass.check("Bash", {}) is True)
check("bypass: Write 通过", pm_bypass.check("Write", {}) is True)

# acceptEdits：write 通过（read/write 自动），bash 需确认（非交互自动通过）
pm_ae = PermissionManager(PermissionMode.ACCEPT_EDITS)
check("acceptEdits: Write 通过", pm_ae.check("Write", {}) is True)
check("acceptEdits: Edit 通过", pm_ae.check("Edit", {}) is True)

# allow/deny 规则
pm_rules = PermissionManager(PermissionMode.PLAN, allow_rules=["Bash"], deny_rules=["Read"])
check("allow_rules: Bash 在 plan 下通过", pm_rules.check("Bash", {}) is True)
check("deny_rules 优先: Read 拒绝", pm_rules.check("Read", {}) is False)

pm_wild = PermissionManager(PermissionMode.DEFAULT, deny_rules=["Web*"])
check("通配 deny: WebSearch 拒绝", pm_wild.check("WebSearch", {}) is False)
check("通配 deny: WebFetch 拒绝", pm_wild.check("WebFetch", {}) is False)
check("非匹配: Read 通过", pm_wild.check("Read", {}) is True)

# ── 3c Memory 3 层 ──
print("\n[3c] Memory 3 层（全局 / 项目级 / auto-memory）")
import tempfile
from pathlib import Path
from mycode.harness.memory import MemoryManager

with tempfile.TemporaryDirectory() as tmp:
    home = Path(tmp) / "home"
    cwd = Path(tmp) / "proj"
    home.mkdir()
    cwd.mkdir()
    (home / "CLAUDE.md").write_text("全局记忆内容", encoding="utf-8")
    (cwd / "AGENTS.md").write_text("项目记忆内容", encoding="utf-8")
    (home / "memory").mkdir()
    (home / "memory" / "MEMORY.md").write_text("- [x](x.md) — hook", encoding="utf-8")

    mm = MemoryManager(cwd=str(cwd), home=str(home))
    layers = mm.load_layers()
    check("3 层都加载", "global" in layers and any(k.startswith("project") for k in layers) and "auto_memory_index" in layers, str(list(layers.keys())))
    section = mm.to_prompt_section()
    check("生成 # Memory 段", section.startswith("# Memory"))
    check("含全局内容", "全局记忆内容" in section)
    check("含项目内容", "项目记忆内容" in section)
    check("含 auto-memory 索引", "x.md" in section)

    # 空记忆目录
    empty = Path(tmp) / "empty"
    empty.mkdir()
    mm2 = MemoryManager(cwd=str(empty), home=str(empty))
    check("无记忆返回空串", mm2.to_prompt_section() == "")

# ── 3d Context mgmt (clear_thinking) ──
print("\n[3d] Context mgmt (clear_thinking)")
from mycode.agent.context_management import clear_thinking

msgs = [
    {"role": "assistant", "content": [{"type": "thinking", "thinking": "old"}, {"type": "text", "text": "a"}]},
    {"role": "assistant", "content": [{"type": "thinking", "thinking": "new"}, {"type": "text", "text": "b"}]},
]
out = clear_thinking(msgs, keep_recent=1)
check("旧 thinking 被清除", all(b.get("type") != "thinking" for b in out[0]["content"]))
check("新 thinking 保留", any(b.get("type") == "thinking" for b in out[1]["content"]))
check("text 保留", any(b.get("type") == "text" for b in out[0]["content"]))

# ── 3e Skills 目录结构 ──
print("\n[3e] Skills 目录结构")
from mycode.harness.skills import SkillManager as SM

with tempfile.TemporaryDirectory() as tmp:
    d = Path(tmp) / "myskill"
    (d / "agents").mkdir(parents=True)
    (d / "scripts").mkdir()
    (d / "agents" / "a.md").write_text("x", encoding="utf-8")
    (d / "scripts" / "s.sh").write_text("y", encoding="utf-8")
    res = SM._scan_resources(d)
    check("扫描到 agents", "agents" in res and "a.md" in res["agents"], str(res))
    check("扫描到 scripts", "scripts" in res and "s.sh" in res["scripts"], str(res))

# ── 3f Settings 4 层级 ──
print("\n[3f] Settings 4 层级")
from mycode.harness.settings import Settings

with tempfile.TemporaryDirectory() as tmp:
    home = Path(tmp) / "home"
    cwd = Path(tmp) / "proj"
    managed = Path(tmp) / "managed.json"
    home.mkdir()
    (cwd / ".mycode").mkdir(parents=True)
    managed.write_text('{"model":"managed-model","a":1}', encoding="utf-8")
    (home / "settings.json").write_text('{"model":"user-model","b":2}', encoding="utf-8")
    (cwd / ".mycode" / "settings.json").write_text('{"b":3}', encoding="utf-8")
    (cwd / ".mycode" / "settings.local.json").write_text('{"c":4}', encoding="utf-8")
    s = Settings(cwd=str(cwd), home=str(home), managed_path=str(managed))
    s.load()
    check("4 层都加载", set(s.loaded_layers) == {"managed", "user", "project", "local"}, str(s.loaded_layers))
    check("user 覆盖 managed (model)", s.get("model") == "user-model", str(s.get("model")))
    check("project 覆盖 user (b)", s.get("b") == 3, str(s.get("b")))
    check("local 层生效 (c)", s.get("c") == 4)

# ── 3g Plugins ──
print("\n[3g] Plugins")
from mycode.harness.plugins import PluginManager

with tempfile.TemporaryDirectory() as tmp:
    pdir = Path(tmp) / "plugins"
    pdir.mkdir(parents=True)
    (pdir / "installed_plugins.json").write_text('[{"name":"p1"},{"name":"p2"}]', encoding="utf-8")
    pm = PluginManager(home=tmp)
    check("加载已安装插件", [p["name"] for p in pm.list_installed()] == ["p1", "p2"], str(pm.list_installed()))

    class FakeS:
        def get(self, k, d=None):
            return {"enabledPlugins": {"p1": True, "p2": False}}.get(k, d)

    check("enabled 过滤", pm.enabled_names(FakeS()) == ["p1"])

print(f"\n=== 结果: {PASS} PASS / {FAIL} FAIL ===")
sys.exit(0 if FAIL == 0 else 1)