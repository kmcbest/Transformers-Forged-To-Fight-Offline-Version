import sys
import ctypes
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

from sim_server import g_engine
from Server.abilities.bots.blackout import build_blackout_abilities

# HitResultFlags constants
HIT_FLAG_HIT          = 0x0001
HIT_FLAG_MISSED       = 0x0002
HIT_FLAG_BLOCKED      = 0x0004
HIT_FLAG_INVULNERABLE = 0x0018
HIT_FLAG_LAST_HIT     = 0x0080
HIT_FLAG_PROJECTILE   = 0x0100
HIT_FLAG_AVOIDED      = 0x0200
HIT_FLAG_EVADED       = 0x0400
HIT_FLAG_CANCELLED    = 0x0800
HIT_FLAG_REFLECTED    = 0x1000

def assert_true(cond, msg):
    if not cond:
        print(f"  ❌ [FAIL] {msg}")
        sys.exit(1)
    else:
        print(f"  ✅ [PASS] {msg}")

def has_buff(state, player_key, substr):
    return any(substr in b["id"] for b in state[player_key]["buffs"])

def get_buff_stacks(state, player_key, substr):
    for b in state[player_key]["buffs"]:
        if substr in b["id"]:
            return b["stacks"]
    return 0

# Bind new C exports
lib = g_engine.dll
lib.sim_fire_attack_ended.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint32, ctypes.c_float]
lib.sim_fire_attack_ended.restype = None
lib.sim_fire_special_state.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int]
lib.sim_fire_special_state.restype = None

print("===========================================================================")
print("🤖 眩晕 (Blackout) 全机制 + 统一“落空”状态机自动化门禁测试")
print("===========================================================================")

# 1. Data contract check (Python StatMods & Appearances)
print("\n--- [TEST 1] 数据契约与删除项核验 ---")
mods, appears, _ = build_blackout_abilities()
assert_true("blackout_gatling_ranged_buff" not in mods, "加特林机枪已彻底移除")
assert_true("blackout_sp2_crit_resist_debuff" not in mods, "SP2 暴击抗性减益不存在")
assert_true("blackout_sp1_crit_resist_debuff" not in mods, "SP1 暴击抗性减益已彻底从 mods 中移除")
assert_true("blackout_sp1_crit_damage" in mods and mods["blackout_sp1_crit_damage"]["m"] == 0.35 and mods["blackout_sp1_crit_damage"]["d"] == 3.5, "SP1 暴击伤害 (+35%, 3.5s) 定义正确")
assert_true(mods["blackout_sp2_crit_damage"]["m"] == 0.60, "SP2 暴击伤害已修正为 60%")
assert_true(mods["blackout_sp2_crit_bleed"]["st"] >= 10, "SP2 暴击流血支持可叠加 (st=%d)" % mods["blackout_sp2_crit_bleed"]["st"])
assert_true(mods["blackout_sp3_crit_resist_debuff"]["st"] >= 10 and mods["blackout_sp3_crit_resist_debuff"]["tr"] == [], "SP3 永久暴抗减益可叠加且无重复自动触发器")
assert_true(appears["appr_blackout_sp1_unblockable"]["tc"] == "C4BBF8", "SP1 不可防御图标为浅紫色 (C4BBF8)")
assert_true(mods["blackout_sig_whiff_power_gain"]["t"] == "modify_stat" and mods["blackout_sig_whiff_power_gain"]["m"] == 0.0 and mods["blackout_sig_whiff_power_gain"]["d"] == 3.0, "追猎图标为纯 3 秒冷却提示，杜绝双倍回能")

# 2. Unified Miss State Machine (追猎)
print("\n--- [TEST 2] 统一“落空”状态机 & 追猎 (瞬时+6%能量 + 3秒CD) ---")
g_engine.init("blackout_cin_tf", "ironhide_gs_kabam", 40519.0, 40000.0, 3272.0, 3000.0)
g_engine.reset()
g_engine.tick(100)
st0 = g_engine.get_state()
mana0 = st0["p0"]["mana"]

# 2a. 命中(Hit) / 格挡(Blocked) / 对波抵消(Cancelled) / 被反射(Reflected) / S1~S3落空 绝不触发
lib.sim_fire_attack_ended(0, 1, 0, HIT_FLAG_HIT, 500.0)
lib.sim_fire_attack_ended(0, 2, 0, HIT_FLAG_BLOCKED, 100.0)
lib.sim_fire_attack_ended(0, 8, 0, HIT_FLAG_PROJECTILE | HIT_FLAG_MISSED | HIT_FLAG_CANCELLED, 0.0)
lib.sim_fire_attack_ended(0, 8, 0, HIT_FLAG_PROJECTILE | HIT_FLAG_INVULNERABLE | HIT_FLAG_REFLECTED, 0.0)
lib.sim_fire_attack_ended(0, 16, 0, HIT_FLAG_MISSED, 0.0)
lib.sim_fire_attack_ended(0, 32, 0, HIT_FLAG_MISSED, 0.0)
lib.sim_fire_attack_ended(0, 64, 0, HIT_FLAG_MISSED, 0.0)
st = g_engine.get_state()
assert_true(abs(st["p0"]["mana"] - mana0) < 0.001 and not has_buff(st, "p0", "blackout_sig_whiff_power_gain"),
            "Hit / Blocked / 对波Cancelled / 反射Reflected / S1~S3落空 均不触发追猎")

# 2b. 近战轻击落空 -> 瞬间 +6% (0.18 格) + 3秒倒计时图标
lib.sim_fire_attack_ended(0, 1, 0, HIT_FLAG_MISSED, 0.0)
st = g_engine.get_state()
assert_true(abs(st["p0"]["mana"] - (mana0 + 0.18)) < 0.01 and has_buff(st, "p0", "blackout_sig_whiff_power_gain"),
            f"近战轻击落空瞬间到账 +6% 能量 (mana={st['p0']['mana']:.2f}) 并点亮 3 秒冷却图标")

# 2c. 3 秒冷却期内再次远程落空 -> 不重复触发
g_engine.tick(1500)
mana_before_cd = g_engine.get_state()["p0"]["mana"]
lib.sim_fire_attack_ended(0, 8, 0, HIT_FLAG_PROJECTILE | HIT_FLAG_MISSED, 0.0)
st = g_engine.get_state()
assert_true(abs(st["p0"]["mana"] - mana_before_cd) < 0.001, "3 秒倒计时结束前再次落空不可重复触发")

# 2d. 冷却结束后远程落空 (含前冲穿弹 -> Projectile|Missed) -> 再次 +6%
g_engine.tick(2000) # total 3500ms > 3000ms
mana_after_cd = g_engine.get_state()["p0"]["mana"]
lib.sim_fire_attack_ended(0, 8, 0, HIT_FLAG_PROJECTILE | HIT_FLAG_MISSED, 0.0)
st = g_engine.get_state()
assert_true(abs(st["p0"]["mana"] - (mana_after_cd + 0.18)) < 0.01, "冷却结束后远程落空/前冲穿弹再次触发 +6% 能量")

# 2e. 冷却结束后重击被规避 (Evaded) -> 再次 +6%
g_engine.tick(3200)
mana_before_heavy = g_engine.get_state()["p0"]["mana"]
lib.sim_fire_attack_ended(0, 4, 0, HIT_FLAG_INVULNERABLE | HIT_FLAG_EVADED, 0.0)
st = g_engine.get_state()
assert_true(abs(st["p0"]["mana"] - (mana_before_heavy + 0.18)) < 0.01, "重击被规避 (Evaded) 触发追猎 +6% 能量")

# 3. SP1 浅紫色不可防御时间窗 + 技能期间 35% 暴击伤害
print("\n--- [TEST 3] SP1 浅紫色不可防御图标时间窗 & 技能期间 35% 暴伤 ---")
g_engine.reset()
g_engine.tick(100)
lib.sim_fire_special_state(0, 1, 1) # SP1 enter
st = g_engine.get_state()
assert_true(has_buff(st, "p0", "blackout_sp1_crit_damage"), "SP1 启动 -> 获得 35% 暴击伤害增益")
assert_true(not has_buff(st, "p0", "blackout_sp1_unblockable"), "SP1 刚起手第一击前，不提前亮不可防御图标")

# SP1 Hit 0 ends -> last-hit unblockable window opens!
lib.sim_fire_attack_ended(0, 16, 0, HIT_FLAG_HIT, 300.0)
st = g_engine.get_state()
assert_true(has_buff(st, "p0", "blackout_sp1_unblockable"), "SP1 第一击结束进入最后一击阶段 -> 浅紫色不可防御图标亮起")

# SP1 Last Hit connects -> 不再施加旧的暴击抗性减益
g_engine.attack(0, 16, 1, 1, 0) # P0 SP1 last hit (not blocked)
st = g_engine.get_state()
assert_true(not has_buff(st, "p1", "blackout_sp1_crit_resist_debuff"), "SP1 最后一击命中 -> 不再施加已移除的暴击抗性减益")

# SP1 Last Hit ends -> light-purple icon vanishes immediately!
lib.sim_fire_attack_ended(0, 16, 100, HIT_FLAG_PROJECTILE | HIT_FLAG_HIT | HIT_FLAG_LAST_HIT, 700.0)
lib.sim_fire_special_state(0, 1, 0) # SP1 exit
st = g_engine.get_state()
assert_true(not has_buff(st, "p0", "blackout_sp1_unblockable"), "SP1 最后一击结算完毕 -> 浅紫色不可防御图标立即消失")
assert_true(not has_buff(st, "p0", "blackout_sp1_crit_damage"), "SP1 退出瞬间 -> 35% 暴击伤害增益立即移除，绝不残留")

# 4. SP2 60% 暴伤严格限定在技能期间
print("\n--- [TEST 4] SP2 60% 暴击伤害严格限定在技能期间 ---")
lib.sim_fire_special_state(0, 2, 1) # SP2 enter
st = g_engine.get_state()
assert_true(has_buff(st, "p0", "blackout_sp2_crit_damage"), "SP2 启动 -> 获得 60% 暴击伤害增益")

lib.sim_fire_special_state(0, 2, 0) # SP2 exit
st = g_engine.get_state()
assert_true(not has_buff(st, "p0", "blackout_sp2_crit_damage"), "SP2 退出瞬间 -> 60% 暴击伤害增益立即移除，绝不残留")

# 5. SP2 退出后 SP1 不误伤流血、加特林彻底不存在
print("\n--- [TEST 5] 连续 3 次远程射击绝不再触发加特林机枪 ---")
for _ in range(4):
    g_engine.attack(0, 8, 0, 0, 1)
    g_engine.tick(200)
st = g_engine.get_state()
assert_true(not has_buff(st, "p0", "gatling"), "连续远程射击不再触发已删除的加特林机枪")

print("\n===========================================================================")
print("✨ 恭喜！眩晕全机制与统一“落空”状态机全部通过自动化门禁测试！")
print("===========================================================================")
