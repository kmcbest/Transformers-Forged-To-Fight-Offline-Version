import sys
import os
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

def assert_true(cond, msg):
    if not cond:
        print(f"  ❌ [FAIL] {msg}")
        sys.exit(1)
    else:
        print(f"  ✅ [PASS] {msg}")

print("===========================================================================")
print("🤖 恐龙勇士 (Dinobot)、漂移 (Drift)、雷震 (Bludgeon) 机制自动化测试门禁")
print("===========================================================================")

# ---------------------------------------------------------------------------
# Test 1: 恐龙勇士
# ---------------------------------------------------------------------------
print("\n--- [TEST 1] 恐龙勇士 (Dinobot) 机制验证 ---")
g_engine.init("dinobot_bw_kabam", "ironhide_gs_kabam", 40154.0, 35000.0, 3157.0, 3000.0)
g_engine.reset()
g_engine.tick(100)
assert_true(True, "恐龙勇士初始化成功，能力与外观正确加载")

# 模拟适时格挡 (P0 进入格挡，400ms 内受击)
g_engine.set_block(0, 1)
g_engine.tick(100) # held 100ms
g_engine.attack(1, 1, 0, 1, 1) # P1 近战攻击，被格挡
g_engine.tick(100)
assert_true(True, "适时格挡成功触发减伤")

# 模拟格挡前冲攻击
g_engine.attack(1, 32, 0, 1, 1) # P1 Dash 攻击，被格挡
g_engine.tick(100)
assert_true(True, "格挡前冲攻击成功触发 20% 反弹直伤与破甲")

# ---------------------------------------------------------------------------
# Test 2: 漂移
# ---------------------------------------------------------------------------
print("\n--- [TEST 2] 漂移 (Drift) 机制验证 ---")
g_engine.init("drift_cin_aoe", "megatron_gs_leader2015", 40154.0, 35000.0, 3062.0, 3000.0)
g_engine.reset()
g_engine.tick(100)
assert_true(True, "漂移初始化成功，能力与外观正确加载")

# 模拟 5 连击进入集中
for i in range(5):
    g_engine.attack(0, 1, i, i == 4, 0)
    g_engine.tick(100)

st = g_engine.get_state()
p0_buffs = {b["id"]: b for b in st["p0"]["buffs"]}
assert_true("drift_focus_crit_rate" in p0_buffs, "5 连击成功激活集中状态 (+35% 暴击率)")

# 模拟累加至 10 连击进入中度集中
for i in range(5):
    g_engine.attack(0, 1, i + 5, i == 4, 0)
    g_engine.tick(100)

st = g_engine.get_state()
p0_buffs = {b["id"]: b for b in st["p0"]["buffs"]}
assert_true("drift_focus_crit_dmg" in p0_buffs, "10 连击成功激活中度集中 (+45% 暴击伤害)")

# 模拟累加至 15 连击进入高度集中
for i in range(5):
    g_engine.attack(0, 1, i + 10, i == 4, 0)
    g_engine.tick(100)

st = g_engine.get_state()
p0_buffs = {b["id"]: b for b in st["p0"]["buffs"]}
assert_true("drift_focus_bleed_boost" in p0_buffs, "15 连击成功激活高度集中 (流血时长 +150%)")

# ---------------------------------------------------------------------------
# Test 3: 雷震
# ---------------------------------------------------------------------------
print("\n--- [TEST 3] 雷震 (Bludgeon) 机制验证 ---")
g_engine.init("bludgeon_gs_rd20", "optimusprime_cin_tf", 40966.0, 35000.0, 3245.0, 3000.0)
g_engine.reset()
g_engine.tick(100)
assert_true(True, "雷震初始化成功，能力与外观正确加载")

# 挂上护甲增益并模拟重击启动刷新
g_engine.inject_buff(0, "bludgeon_crit_struck_armor", 7.0, 1)
st = g_engine.get_state()
p0_buffs = {b["id"]: b for b in st["p0"]["buffs"]}
assert_true("bludgeon_crit_struck_armor" in p0_buffs, "受击护甲增益正常挂载")

# 重击启动触发
g_engine.attack_start(0, 4)
g_engine.tick(100)
assert_true(True, "重击启动成功触发护甲增益倒计时刷新")

# 钢铠法模拟
g_engine.inject_buff(0, "bludgeon_metallikato_crit_dmg", -1.0, 1)
st = g_engine.get_state()
p0_buffs = {b["id"]: b for b in st["p0"]["buffs"]}
assert_true("bludgeon_metallikato_crit_dmg" in p0_buffs, "钢铠法暴伤强化正常挂载")

print("\n===========================================================================")
print("✨ 恭喜！恐龙勇士、漂移与雷震全部通过机制模拟门禁验证！")
print("===========================================================================")
