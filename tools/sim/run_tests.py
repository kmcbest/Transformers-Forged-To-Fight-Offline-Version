#!/usr/bin/env python3
"""
TFTF Combat Simulator Automated Quality Gate Test Suite
======================================================
Tests all native skill logic in 0.2s without mobile device or APK.
"""
import sys
import json
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


# Add sim directory
sys.path.insert(0, str(Path(__file__).resolve().parent))
from sim_server import g_engine

def assert_true(cond, msg):
    if not cond:
        print(f"[FAIL] {msg}")
        sys.exit(1)
    else:
        print(f"  [PASS] {msg}")

def test_optimus_mv_willpower():
    print("\n--- [TEST 1] Movie Optimus: Bleed Purify & Willpower Lifesteal ---")
    g_engine.init("optimusprime_cin_tf", "bonecrusher_cin_rotf", 15000.0, 15000.0, 1000.0, 1000.0)

    # 1. 注入 2 层流血
    g_engine.inject_buff(0, "dmg_bleed", 6.0, 2)
    st = g_engine.get_state()
    assert_true(len(st["p0"]["buffs"]) == 1 and st["p0"]["buffs"][0]["stacks"] == 2, "2 stacks of bleed applied to Optimus")

    # 2. 推进 1.1s 时间
    g_engine.tick(1100)
    st = g_engine.get_state()
    buffs = {b["id"]: b["stacks"] for b in st["p0"]["buffs"]}
    assert_true("dmg_bleed" in buffs and buffs["dmg_bleed"] == 1, "Exactly 1 bleed stack remains (1 purified)")
    assert_true(abs(st["p0"]["mana"] - 0.30) < 0.01, f"Optimus gained 10% mana (0.30 bars), actual: {st['p0']['mana']}")

    # 3. 带着 1 层流血打出重击 (伤害应有 35% 转化为自身生命)
    dmg = g_engine.attack(0, 4, 0, 1, 0)
    logs = g_engine.pop_logs()
    floaters = g_engine.pop_floaters()
    heal_floaters = [f for f in floaters if f["type"] == 2]
    assert_true(len(heal_floaters) > 0, f"Lifesteal floater emitted: {heal_floaters}")
    expected_heal = dmg * 0.35
    actual_heal = heal_floaters[0]["val"]
    assert_true(abs(actual_heal - expected_heal) < 1.0, f"Heal amount matches 35% damage ({actual_heal} == {expected_heal})")

def test_megatron_debuff_fusion():
    print("\n--- [TEST 2] G1 Megatron: Debuff Fusion to Permanent ---")
    g_engine.init("megatron_gs_leader2015", "sharkticon_gs_demolition", 15000.0, 15000.0, 1000.0, 1000.0)

    # 1. 给威震天注入 3 层融合炮
    g_engine.inject_buff(0, "megatron_fusion_cannon", -1.0, 3)

    # 2. 给敌方鲨鱼精注入带倒计时的震击与破甲
    g_engine.inject_buff(1, "megatron_sp3_shock", 8.0, 1)
    g_engine.inject_buff(1, "megatron_sp1_armor_break", 8.0, 1)

    st_before = g_engine.get_state()
    assert_true(len(st_before["p1"]["buffs"]) == 2, "Enemy has 2 timed debuffs before hit")
    assert_true(all(b["rem_ms"] > 0 for b in st_before["p1"]["buffs"]), "Both enemy debuffs have countdown timer")

    # 3. 威震天全功率重击命中
    g_engine.attack(0, 4, 0, 1, 0)
    st_after = g_engine.get_state()

    # 验证融合炮消耗 1 层
    p0_buffs = {b["id"]: b["stacks"] for b in st_after["p0"]["buffs"]}
    assert_true(p0_buffs.get("megatron_fusion_cannon", 0) == 2, "Fusion cannon consumed 1 stack (3 -> 2)")

    # 验证敌方 2 个减益转化为永久 (-1ms)
    p1_buffs = st_after["p1"]["buffs"]
    assert_true(all(b["rem_ms"] == -1 for b in p1_buffs), "All debuffs on enemy successfully FUSED to permanent (-1ms)")

    # 验证 HUD 广播
    assert_true("减益融合" in st_after["announcement"], f"Announcement displayed fusion message: {st_after['announcement']}")

def test_prowl_melee_buff():
    print("\n--- [TEST 3] Prowl: 10 Stacks Melee Buff Scaling ---")
    g_engine.init("prowl_gs_deluxe2010", "bonecrusher_cin_rotf", 15000.0, 15000.0, 1000.0, 1000.0)

    # 基础伤害
    base_dmg = g_engine.attack(0, 1, 0, 0, 0)

    # 注入 10 层近战增益
    g_engine.inject_buff(0, "prowl_melee_buff", 6.0, 10)
    boosted_dmg = g_engine.attack(0, 1, 0, 0, 0)

    assert_true(boosted_dmg > base_dmg, f"Boosted damage ({boosted_dmg}) > base damage ({base_dmg})")

def test_prowl_dash_back_charge():
    print("\n--- [TEST 4] Prowl: Dash Back Charge & Attack Convert ---")
    g_engine.init("prowl_gs_deluxe2016", "bonecrusher_cin_rotf", 15000.0, 15000.0, 1000.0, 1000.0)
    g_engine.reset()

    # 1. 警车后闪 (type=0)
    g_engine.dodge(0, 0)
    st = g_engine.get_state()
    p0_buffs = {b["id"]: b for b in st["p0"]["buffs"]}
    assert_true("prowl_melee_charge" in p0_buffs, "Prowl started charging with prowl_melee_charge")
    assert_true(p0_buffs["prowl_melee_charge"]["stacks"] == 1, "Initial charge is 1 stack")

    # 2. 推进时间 1500ms (应递增 3 次 -> 达到 4 层)
    for _ in range(15):
        g_engine.tick(100)
    st = g_engine.get_state()
    p0_buffs = {b["id"]: b for b in st["p0"]["buffs"]}
    stacks = p0_buffs["prowl_melee_charge"]["stacks"]
    assert_true(stacks >= 4, f"Charge stacks increased with time (expected >=4, actual {stacks})")

    # 3. 警车出招 -> 打断充能并转化为近战增益
    g_engine.attack(0, 1, 0, 0, 0)
    st = g_engine.get_state()
    p0_buffs = {b["id"]: b for b in st["p0"]["buffs"]}
    assert_true("prowl_melee_charge" not in p0_buffs, "Charging buff cleared on attack")
    assert_true("prowl_melee_buff" in p0_buffs, "Converted to orange prowl_melee_buff")
    assert_true(p0_buffs["prowl_melee_buff"]["stacks"] == stacks, f"Melee buff has {stacks} stacks")

def test_bumblebee_sidestep_crit():
    print("\n--- [TEST 5] Bumblebee: Sidestep Crit Buff Stacking ---")
    g_engine.init("bumblebee_gs_kabam", "bonecrusher_cin_rotf", 15000.0, 15000.0, 1000.0, 1000.0)
    g_engine.reset()

    # 侧闪 1 次 (type=1)
    g_engine.dodge(0, 1)
    st = g_engine.get_state()
    p0_buffs = {b["id"]: b for b in st["p0"]["buffs"]}
    assert_true("bumblebee_crit_buff" in p0_buffs, "Bumblebee gained crit buff on sidestep")
    assert_true(p0_buffs["bumblebee_crit_buff"]["stacks"] == 1, "First sidestep is 1 stack")

    # 再次侧闪 2 次 (最多 3 层)
    g_engine.dodge(0, 1)
    g_engine.dodge(0, 1)
    g_engine.dodge(0, 1) # 第4次不应超过3层
    st = g_engine.get_state()
    p0_buffs = {b["id"]: b for b in st["p0"]["buffs"]}
    assert_true(p0_buffs["bumblebee_crit_buff"]["stacks"] == 3, "Crit buff capped at 3 stacks")

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 TFTF 战斗技能模拟器本地全自动化质量门禁测试")
    print("=" * 60)
    test_optimus_mv_willpower()
    test_megatron_debuff_fusion()
    test_prowl_melee_buff()
    test_prowl_dash_back_charge()
    test_bumblebee_sidestep_crit()
    print("\n" + "=" * 60)
    print("🎉 全部测试 100% 通过！底层 C 技能模块在 PC 端完美通过逻辑闭环！")
    print("=" * 60)
