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

from sim_server import g_engine, CURRENT_MATCHUP, trigger_onstart_phase
from Server.abilities.bots.nemesisprime import build_nemesisprime_abilities


def assert_true(cond, msg):
    if not cond:
        print(f"  ❌ [FAIL] {msg}")
        sys.exit(1)
    else:
        print(f"  ✅ [PASS] {msg}")


def has_buff(state, player_key, substr):
    return any(substr in b["id"] for b in state[player_key]["buffs"])


def get_buff(state, player_key, substr):
    for b in state[player_key]["buffs"]:
        if substr in b["id"]:
            return b
    return None


print("===========================================================================")
print("🤖 暗天陨 (Nemesis Prime) 全套技能自动化门禁测试")
print("===========================================================================")

# TEST 1: 数据契约核验
print("\n--- [TEST 1] 数据契约与图标核验 ---")
mods, appears = build_nemesisprime_abilities()
assert_true(appears["appr_nemesisprime_dark_cd"]["t"] == "\uE407", "黑暗能量倒计时图标为 E407")
assert_true(appears["appr_nemesisprime_dark_energy"]["t"] == "\uE90A", "黑暗能量充能图标为 E90A")
assert_true(appears["appr_nemesisprime_heavy_dispel"]["t"] == "\uE950", "重击驱散图标为 E950")
assert_true(appears["appr_nemesisprime_matrix_lifesteal"]["t"] == "\uE503", "赝品领导模块图标为 E503")
assert_true(mods["nemesisprime_matrix_lifesteal"]["t"] == "combat", "赝品领导模块走 C 层实际伤害 25% 吸血，不发固定回血")
assert_true(mods["nemesisprime_sp3_unblockable"]["t"] == "unblockable", "SP3 不可防御类型为原生 unblockable")
assert_true("nemesisprime_sp2_melee_debuff" in mods and "nemesisprime_sp2_armor_break" in mods, "SP2 近战减益与破甲修饰器均已注册")

# TEST 2: 黑暗能量周期充能 (10s -> 5s 低血加速 -> 满 10 层隐藏倒计时)
print("\n--- [TEST 2] 黑暗能量周期充能与低血量加速核验 ---")
CURRENT_MATCHUP["p0_bot_id"] = "nemesisprime_gs_voyager2015"
CURRENT_MATCHUP["p1_bot_id"] = "ironhide_gs_kabam"
g_engine.init("nemesisprime_gs_voyager2015", "ironhide_gs_kabam", 31500.0, 32000.0, 2380.0, 2400.0)
g_engine.reset()
trigger_onstart_phase()
st = g_engine.get_state()
assert_true(has_buff(st, "p0", "nemesisprime_dark_cd"), "开局挂载黑暗能量倒计时 E407")

# 推进 10.1 秒获得第 1 层
for _ in range(101):
    g_engine.tick(100)
st = g_engine.get_state()
de = get_buff(st, "p0", "nemesisprime_dark_energy")
assert_true(de is not None and de["stacks"] == 1, f"满血 10 秒获得第 1 层黑暗能量 (actual={de})")

# 压低血量至 <15%，5 秒获得第 2 层
g_engine.set_hp(0, 31500.0 * 0.12)
for _ in range(51):
    g_engine.tick(100)
st = g_engine.get_state()
de = get_buff(st, "p0", "nemesisprime_dark_energy")
assert_true(de is not None and de["stacks"] == 2, f"<15% 血量加速至 5 秒获得第 2 层 (actual={de})")

# 注入至 10 层应消除倒计时
for _ in range(8):
    g_engine.inject_buff(0, "nemesisprime_dark_energy", -1.0, 1)
st = g_engine.get_state()
de = get_buff(st, "p0", "nemesisprime_dark_energy")
assert_true(de is not None and de["stacks"] == 10, "堆叠至上限 10 层黑暗能量")
assert_true(not has_buff(st, "p0", "nemesisprime_dark_cd"), "满 10 层后黑暗能量倒计时图标自动消失")

# TEST 3: 亚空间脉冲克隆体 (25%+5%/层, 10层=75% 复制对手护甲/近战增益)
print("\n--- [TEST 3] 亚空间脉冲克隆体复制对手增益核验 ---")
cloned = False
for _ in range(20):
    g_engine.inject_buff(1, "ironhide_passive_armor_up", 10.0, 1)
    if has_buff(g_engine.get_state(), "p0", "ironhide_passive_armor_up"):
        cloned = True
        break
assert_true(cloned, "暗天陨成功克隆对手的护甲增益并保持原修饰器 ID 与时间")

# TEST 4: 重击驱散 + 每层 +5% 重击增伤
print("\n--- [TEST 4] 重击随机驱散与 10 层重击 +50% 增伤核验 ---")
g_engine.reset()
g_engine.tick(100)
hp_b0 = g_engine.get_state()["p1"]["hp"]
g_engine.attack(0, 4, 0, 1, 0)  # 0 层重击基线
dmg_0 = hp_b0 - g_engine.get_state()["p1"]["hp"]

g_engine.reset()
g_engine.tick(100)
for _ in range(10):
    g_engine.inject_buff(0, "nemesisprime_dark_energy", -1.0, 1)
g_engine.inject_buff(1, "ironhide_sp1_melee_buff", 8.0, 1)
hp_b10 = g_engine.get_state()["p1"]["hp"]
g_engine.attack(0, 4, 0, 1, 0)  # 10 层重击 (+50%) 且驱散对手近战增益
dmg_10 = hp_b10 - g_engine.get_state()["p1"]["hp"]
st = g_engine.get_state()
assert_true(dmg_10 > dmg_0 * 1.40, f"10 层黑暗能量重击伤害约 +50% ({dmg_0:.1f} -> {dmg_10:.1f})")
assert_true(not has_buff(st, "p1", "ironhide_sp1_melee_buff"), "重击命中成功随机驱散对手近战增益")

# TEST 5: 觉醒赝品领导模块 (25% 实际特技伤害吸血) + SP1 复制自身减益 + 结束 +2 层
print("\n--- [TEST 5] 觉醒特技吸血 & SP1 复制减益 +2 层核验 ---")
g_engine.reset()
g_engine.set_hp(0, 31500.0 * 0.40)
hp_before = g_engine.get_state()["p0"]["hp"]
g_engine.inject_buff(0, "arcee_sp2_bleed", 4.0, 1)
for _ in range(10):
    g_engine.inject_buff(0, "nemesisprime_dark_energy", -1.0, 1)
# SP1 末击 (60% 概率复制)，确保至少成功 1 次
cloned_debuff = False
for _ in range(15):
    g_engine.attack(0, 16, 2, 1, 0)
    if has_buff(g_engine.get_state(), "p1", "arcee_sp2_bleed"):
        cloned_debuff = True
        break
hp_after = g_engine.get_state()["p0"]["hp"]
assert_true(hp_after > hp_before + 100.0, f"特技命中将实际伤害 25% 转化为生命值 ({hp_before:.1f} -> {hp_after:.1f})")
assert_true(cloned_debuff, "SP1 黑暗能量斩末击成功将自身减益复制至对手")

g_engine.reset()
g_engine.tick(100)
g_engine.dll.sim_fire_special_state(0, 1, 1)
g_engine.dll.sim_fire_special_state(0, 1, 0)
de = get_buff(g_engine.get_state(), "p0", "nemesisprime_dark_energy")
assert_true(de is not None and de["stacks"] == 2, f"SP1 结束立即获得 2 层黑暗能量 (actual={de})")

# TEST 6: SP2 邪恶之斧 (驱散近战/护甲增益 -> 5%减益/破甲 4s, 每驱散消耗 3 层)
print("\n--- [TEST 6] SP2 邪恶之斧双分支驱散与消耗 3 层核验 ---")
g_engine.reset()
for _ in range(10):
    g_engine.inject_buff(0, "nemesisprime_dark_energy", -1.0, 1)
g_engine.inject_buff(1, "ironhide_sp1_melee_buff", 8.0, 1)
g_engine.inject_buff(1, "ironhide_sp2_armor_up", 10.0, 1)
g_engine.attack(0, 32, 0, 0, 0)  # 10 层时驱散概率 = 50% + 50% = 100%!
st = g_engine.get_state()
assert_true(not has_buff(st, "p1", "ironhide_sp1_melee_buff"), "10层时 SP2 100% 驱散对手近战增益")
assert_true(not has_buff(st, "p1", "ironhide_sp2_armor_up"), "10层时 SP2 100% 驱散对手护甲增益")
assert_true(has_buff(st, "p1", "nemesisprime_sp2_melee_debuff"), "驱散近战增益后施加 5% 近战减益")
assert_true(has_buff(st, "p1", "nemesisprime_sp2_armor_break"), "驱散护甲增益后施加 5% 破甲")
de = get_buff(st, "p0", "nemesisprime_dark_energy")
assert_true(de is not None and de["stacks"] == 4, f"驱散 2 个增益消耗 6 层黑暗能量 (10 -> 4, actual={de})")
assert_true(has_buff(st, "p0", "nemesisprime_dark_cd"), "跌破 10 层后自动恢复黑暗能量倒计时图标")

# TEST 7: SP3 不可防御 (7s + 0.5s/层，清空全部黑暗能量)
print("\n--- [TEST 7] SP3 不可防御时长公式与消耗全部层数核验 ---")
g_engine.dll.sim_fire_special_state(0, 3, 1)
g_engine.dll.sim_fire_special_state(0, 3, 0)
st = g_engine.get_state()
assert_true(not has_buff(st, "p0", "nemesisprime_dark_energy"), "SP3 结束清空全部 4 层黑暗能量")
unbl = get_buff(st, "p0", "nemesisprime_sp3_unblockable")
assert_true(unbl is not None and abs(unbl["rem_ms"] - 9000) <= 200, f"4 层对应不可防御时长 7 + 4*0.5 = 9.0s (actual={unbl})")

print("\n===========================================================================")
print("✨ 恭喜！暗天陨 (Nemesis Prime) 全部技能通过自动化门禁测试！")
print("===========================================================================")
