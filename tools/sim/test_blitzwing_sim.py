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
from Server.abilities.bots.blitzwing import build_blitzwing_abilities

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

print("===========================================================================")
print("🤖 闪电 (Blitzwing) 技能与机制自动化门禁测试")
print("===========================================================================")

# 1. 数据契约与 PUA 图标核验 (严格按照技能中枢真理源)
print("\n--- [TEST 1] 数据契约与 PUA 图标核验 ---")
mods, appears, _ = build_blitzwing_abilities()

assert_true(appears["appr_blitzwing_tank_mode"]["t"] == "\uE902", "坦克模式图标为 E902")
assert_true(appears["appr_blitzwing_jet_mode"]["t"] == "\uE184", "飞机模式图标为 E184")
assert_true(appears["appr_blitzwing_tank_armor"]["t"] == "\uE517", "护甲增益图标为 E517 (非空/非旧图标)")
assert_true(appears["appr_blitzwing_jet_crit"]["t"] == "\uE40D", "暴击几率图标为 E40D (非空/非旧E040)")
assert_true(appears["appr_blitzwing_clamp_tank"]["t"] == "\uE923", "抑制夹钳(坦克)图标为 E923")
assert_true(appears["appr_blitzwing_clamp_jet"]["t"] == "\uE923", "抑制夹钳(飞机)图标为 E923")
assert_true(appears["appr_blitzwing_clamp_sp3"]["t"] == "\uE923", "抑制夹钳(SP3)图标为 E923")
assert_true(appears["appr_blitzwing_sp1_armor_break"]["t"] == "\uE516", "SP1 破甲图标为 E516")
assert_true(appears["appr_blitzwing_sp1_attack_debuff"]["t"] == "\uE916", "SP1 攻击减益图标为 E916")
assert_true(appears["appr_blitzwing_sp2_attack_buff"]["t"] == "\uE406", "SP2 攻击增益图标为 E406")
assert_true(appears["appr_blitzwing_sw_armor"]["t"] == "\uE517", "绝处逢生护甲图标为 E517")

# 2. 开局护甲机制核验 (reset 阶段不提前发放，正式战斗首帧才触发倒计时)
print("\n--- [TEST 2] 开局护甲延迟发放核验 ---")
g_engine.init("blitzwing_gs", "ironhide_gs_kabam", 38250.0, 40000.0, 2795.0, 3000.0)
g_engine.reset()
st = g_engine.get_state()
assert_true(has_buff(st, "p0", "blitzwing_tank_mode"), "开局默认进入坦克模式")
assert_true(not has_buff(st, "p0", "blitzwing_tank_armor"), "reset 阶段(开场动画/倒计时)不提前发放护甲，避免倒计时浪费")

# 模拟首个战斗 tick (正式开战)
g_engine.tick(100)
# 由于 50% 概率，多次测试验证能够成功触发
opened_armor = False
for _ in range(20):
    g_engine.reset()
    g_engine.tick(100)
    st = g_engine.get_state()
    if has_buff(st, "p0", "blitzwing_tank_armor"):
        opened_armor = True
        break
assert_true(opened_armor, "正式开战首帧(tick)有 50% 概率获得 5 秒护甲增益")

# 3. 抑制夹钳命中门禁核验 (对方防御绝不施加，L1/L2/L3/M1 绝不施加，仅 L4/M2/重击未被格挡命中时施加)
print("\n--- [TEST 3] 抑制夹钳精确命中门禁核验 ---")
g_engine.reset()
g_engine.tick(100)

# 3a. 对方格挡防御 (is_blocked = 1) -> 即使打出 L4、M2、重击也绝不施加夹钳
for _ in range(50):
    g_engine.attack(0, 1, 3, 1, 1) # L4 blocked
    g_engine.attack(0, 2, 1, 1, 1) # M2 blocked
    g_engine.attack(0, 4, 0, 1, 1) # Heavy blocked
st = g_engine.get_state()
assert_true(not has_buff(st, "p1", "clamp"), "对方格挡防御时，即使遭受 L4/M2/重击 也绝不施加抑制夹钳")

# 3b. L1 / L2 / L3 / M1 (未被格挡命中) -> 绝不触发夹钳
for _ in range(50):
    g_engine.attack(0, 1, 0, 0, 0) # L1 unblocked (非收招段)
    g_engine.attack(0, 1, 1, 0, 0) # L2 unblocked (非收招段)
    g_engine.attack(0, 1, 2, 0, 0) # L3 unblocked (非收招段)
    g_engine.attack(0, 2, 0, 0, 0) # M1 unblocked (非收招段)
st = g_engine.get_state()
assert_true(not has_buff(st, "p1", "clamp"), "L1/L2/L3/M1 即使未被格挡也绝不触发抑制夹钳")

# 3c. L4 (未被格挡命中) -> 20% 概率施加
l4_clamped = False
for _ in range(30):
    g_engine.reset()
    g_engine.tick(100)
    g_engine.attack(0, 1, 3, 1, 0) # L4 unblocked
    st = g_engine.get_state()
    if has_buff(st, "p1", "clamp"):
        l4_clamped = True
        break
assert_true(l4_clamped, "L4 命中未被格挡时正常触发 20% 概率施加夹钳")

# 3d. M2 (未被格挡命中) -> 20% 概率施加
m2_clamped = False
for _ in range(30):
    g_engine.reset()
    g_engine.tick(100)
    g_engine.attack(0, 2, 1, 1, 0) # M2 unblocked
    st = g_engine.get_state()
    if has_buff(st, "p1", "clamp"):
        m2_clamped = True
        break
assert_true(m2_clamped, "M2 命中未被格挡时正常触发 20% 概率施加夹钳")

# 3e. 重击 (未被格挡命中) -> 80% 概率施加
heavy_clamped = False
for _ in range(10):
    g_engine.reset()
    g_engine.tick(100)
    g_engine.attack(0, 4, 0, 1, 0) # Heavy unblocked
    st = g_engine.get_state()
    if has_buff(st, "p1", "clamp"):
        heavy_clamped = True
        break
assert_true(heavy_clamped, "重击命中未被格挡时正常触发 80% 概率施加夹钳")

# 4. 抑制夹钳抵消实战效果核验 (战机夹钳抵消酸雨强酸/破甲等负面减益，坦克夹钳抵消正向增益)
print("\n--- [TEST 4] 抑制夹钳实战抵消机制核验 (战机抵消减益 / 坦克抵消增益) ---")
g_engine.reset()
g_engine.tick(100)

# 4a. 战机夹钳抵消酸雨强酸喷射 (acidstorm_ranged_acid)
g_engine.inject_buff(1, "blitzwing_clamp_jet", 4.0, 1)
res_acid = g_engine.inject_buff(0, "acidstorm_ranged_acid", 4.0, 1)
assert_true(res_acid == 0, "战机夹钳成功拦截酸雨强酸喷射 (acidstorm_ranged_acid)")
st = g_engine.get_state()
assert_true(not has_buff(st, "p1", "blitzwing_clamp_jet"), "抵消减益后战机夹钳正确被消耗")

# 4b. 战机夹钳同击多层减益同免时间窗 (例如重击同时触发酸化侵蚀与破甲)
g_engine.reset()
g_engine.tick(100)
g_engine.inject_buff(1, "blitzwing_clamp_jet", 4.0, 1)
res_heavy_acid = g_engine.inject_buff(0, "acidstorm_heavy_acid", 5.0, 1)
res_heavy_break = g_engine.inject_buff(0, "acidstorm_heavy_acid_break", 5.0, 1)
assert_true(res_heavy_acid == 0, "重击酸化侵蚀被战机夹钳成功拦截")
assert_true(res_heavy_break == 0, "同一击附带的酸蚀破甲在200ms时间窗内一同被免除")
st = g_engine.get_state()
assert_true(not has_buff(st, "p0", "acid"), "闪电自身未受任何酸液腐蚀侵蚀")
assert_true(not has_buff(st, "p0", "break"), "闪电自身未受任何破甲削弱")

# 4c. 坦克夹钳抵消对方正向增益 (acidstorm_acid_boost)
g_engine.inject_buff(1, "blitzwing_clamp_tank", 4.0, 1)
res_boost = g_engine.inject_buff(1, "acidstorm_acid_boost", 5.0, 1)
assert_true(res_boost == 0, "坦克夹钳成功拦截对手正向增益 (acidstorm_acid_boost)")
st = g_engine.get_state()
assert_true(not has_buff(st, "p1", "blitzwing_clamp_tank"), "抵消增益后坦克夹钳正确被消耗")

print("\n===========================================================================")
print("✨ 恭喜！闪电技能与机制全部通过自动化门禁测试！")
print("===========================================================================")
