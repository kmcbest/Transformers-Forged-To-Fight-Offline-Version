#!/usr/bin/env python3
"""
Verification suite for the 3 Combat Sandbox hardware capabilities:
1. Authentic 5/50 roster stats & multi-hit SP/Heavy hit-splits + ranged flags
2. Stun / Knockdown / Action-busy timeline & action gating
3. Block / Heavy Block-Break / Unblockable breakthrough & sim_exec_special
"""
import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

SIM_DIR = Path(__file__).resolve().parent
REPO_ROOT = SIM_DIR.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(SIM_DIR) not in sys.path:
    sys.path.insert(0, str(SIM_DIR))

from sim_server import g_engine, trigger_onstart_phase


def assert_true(cond, msg):
    if not cond:
        print(f"  ❌ [FAIL] {msg}")
        sys.exit(1)
    print(f"  ✅ [PASS] {msg}")


print("===========================================================================")
print("🛠️ 沙盘 3 项硬件能力自动化门禁测试")
print("===========================================================================")

# 1. Authentic 5/50 stats auto-load & SP hit-splits / ranged flags
print("\n--- [TEST 1] 真实 5/50 面板自动加载与多段 SP 拆伤 ---")
g_engine.set_authentic_mode(1)
assert_true(g_engine.get_authentic_mode() == 1, "真实沙盘模式开关已启用")

# Pass 0.0f for HP/ATK so sim_init reads real 5/50 stats from sim_roster_data.h
g_engine.init("arcee_gs_deluxe2014", "ironhide_gs_kabam", 0.0, 0.0, 0.0, 0.0)
st = g_engine.get_state()
assert_true(abs(st["p0"]["max_hp"] - 36098.0) < 1.0, f"阿尔茜 5/50 真实生命值为 36098 (actual={st['p0']['max_hp']})")
assert_true(abs(st["p1"]["max_hp"] - 45427.0) < 1.0, f"铁皮 5/50 真实生命值为 45427 (actual={st['p1']['max_hp']})")

# Trigger Arcee 4-hit SP1 via sim_exec_special
g_engine.set_crit_rate(0, 0.0)  # fix non-crit baseline via crit_rate=0? No, wait: base_crit uses atker->crit_rate
g_engine.set_mana(0, 1.5)
hp_before = g_engine.get_hp(1)
sp1_dmg = g_engine.exec_special(0, 1)
hp_after = g_engine.get_hp(1)
assert_true(sp1_dmg > 0 and abs((hp_before - hp_after) - sp1_dmg) < 5.0,
            f"阿尔茜 sim_exec_special(SP1) 执行多段伤害并真实扣血 (dmg={sp1_dmg})")
assert_true(g_engine.can_act(0) == 0, "阿尔茜刚释放 SP1 后处于动作僵直窗口 (sim_can_act == 0)")

# Advance clock past sp1_dur_ms (2067ms)
for _ in range(25):
    g_engine.tick(100)
assert_true(g_engine.can_act(0) == 1, "推进 2500ms 后动作僵直解除 (sim_can_act == 1)")

# 2. Stun & Knockdown action lock + block auto-cancel
print("\n--- [TEST 2] 眩晕 / 击倒时间轴与行动锁死 ---")
g_engine.reset()
g_engine.set_block(1, 1)
assert_true(g_engine.get_state()["p1"]["is_blocking"] == 1, "P1 进入格挡状态")

# Heavy attack auto-breaks live block when is_blocked == -1 and knocks defender down for 1400ms
heavy_dmg = g_engine.attack(0, 4, 0, 1, -1)
st = g_engine.get_state()
assert_true(st["p1"]["is_blocking"] == 0, "重击自动破防并打断 P1 格挡状态")
assert_true(heavy_dmg > 1000, f"重击破防造成未减免伤害 (dmg={heavy_dmg})")
assert_true(g_engine.is_knocked_down(1) == 1 and g_engine.can_act(1) == 0, "重击命中后 P1 进入击倒状态无法行动")

# Try blocking while knocked down -> must fail in authentic mode
g_engine.set_block(1, 1)
assert_true(g_engine.get_state()["p1"]["is_blocking"] == 0, "击倒期间尝试格挡被物理拒绝")

for _ in range(15):
    g_engine.tick(100)
assert_true(g_engine.is_knocked_down(1) == 0 and g_engine.can_act(1) == 1, "1500ms 后击倒起身恢复行动")

# Stun buff via inject_buff/skill_stun_player: test buff removal / expiry restores action
g_engine.inject_buff(1, "stun", 1.2, 1)
assert_true(g_engine.is_stunned(1) == 1 and g_engine.can_act(1) == 0, "挂载眩晕后 P1 无法行动")
for _ in range(13):
    g_engine.tick(100)
assert_true(g_engine.is_stunned(1) == 0 and g_engine.can_act(1) == 1, "1.3秒后眩晕解除并恢复行动")

# 3. Unblockable breakthrough (Nemesis Prime SP3 vs blocking defender)
print("\n--- [TEST 3] 不可防御穿透 (暗天陨 SP3 穿防) ---")
g_engine.init("nemesisprime_gs_voyager2015", "ironhide_gs_kabam", 0.0, 0.0, 0.0, 0.0)
g_engine.reset()
trigger_onstart_phase()

# Without block on a normal light hit, vs with block on normal light hit:
g_engine.set_block(1, 1)
light_blocked = g_engine.attack(0, 1, 0, 0, -1)
g_engine.set_block(1, 0)
light_unblocked = g_engine.attack(0, 1, 0, 0, -1)
assert_true(light_blocked < light_unblocked, f"普通轻击被自动识别格挡减伤 ({light_blocked} < {light_unblocked})")

# Now Nemesis SP3 while P1 is blocking (unblockable mod + SP3 pierces block)
g_engine.set_block(1, 1)
g_engine.set_mana(0, 3.0)
sp3_dmg = g_engine.exec_special(0, 3)
assert_true(sp3_dmg >= 7000, f"暗天陨 SP3 穿破实时格挡打出全额伤害 (dmg={sp3_dmg})")
assert_true(g_engine.get_state()["p1"]["is_blocking"] == 0, "SP3 命中后 P1 格挡状态被强制打断")

# Restore default legacy mode check
g_engine.set_authentic_mode(0)
assert_true(g_engine.get_authentic_mode() == 0, "可切回旧测试兼容模式")

print("\n🎉 全部沙盘硬件能力门禁测试 PASSED！")
