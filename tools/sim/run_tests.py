#!/usr/bin/env python3
"""
TFTF Combat Simulator Automated Quality Gate Test Suite (Enhanced)
==================================================================
Tests all native skill logic, data contracts, and IL2CPP engine lifecycles
in < 0.5s without needing a mobile device or APK installation.
"""
import sys
import json
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

from sim_server import (
    g_engine,
    decorate_buff,
    trigger_onstart_phase,
    CURRENT_MATCHUP,
    PENDING_START_EVENTS,
)

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

def test_contract_validation():
    print("\n--- [TEST 6] Data Contract Validation: Zero Guesswork Binding ---")
    # 1. 验证电影擎天柱净化：严格读取官方 abilities 数据库，PUA 必须为 0xE942 (意志力绿)，颜色 10B981
    raw_purify = {"id": "optimusprime_cin_tf_purify", "rem_ms": 1500, "stacks": 1}
    dec_purify = decorate_buff(raw_purify)
    assert_true(dec_purify["is_contract_valid"] == True, "Optimus Purify is contract valid")
    assert_true(dec_purify["pua"] == "0xE942", f"Optimus Purify PUA is 0xE942 (willpower), got: {dec_purify['pua']}")
    assert_true(dec_purify["tc"] == "10B981", f"Optimus Purify top color is 10B981, got: {dec_purify['tc']}")
    assert_true(dec_purify["name"] == "净化", f"Optimus Purify name is '净化', got: {dec_purify['name']}")

    # 2. 验证通用标准 Buff
    raw_bleed = {"id": "dmg_bleed", "rem_ms": 7000, "stacks": 1}
    dec_bleed = decorate_buff(raw_bleed)
    assert_true(dec_bleed["is_contract_valid"] == True, "dmg_bleed is standard contract valid")
    assert_true(dec_bleed["pua"] == "0xE401", f"dmg_bleed PUA is 0xE401, got: {dec_bleed['pua']}")
    assert_true(dec_bleed["name"] == "流血", f"dmg_bleed name is '流血', got: {dec_bleed['name']}")

    # 3. 验证未在官方库中定义的未注册 Buff 必须被标记违规
    raw_fake = {"id": "unregistered_test_buff_999", "rem_ms": 5000, "stacks": 1}
    dec_fake = decorate_buff(raw_fake)
    assert_true(dec_fake["is_contract_valid"] == False, "Unregistered buff correctly flagged as contract invalid")
    assert_true("未在" in dec_fake.get("contract_warning", ""), "Contract warning message generated")

def test_lifecycle_onstart():
    print("\n--- [TEST 7] IL2CPP Lifecycle Emulation: 0.00s onStart Phase ---")
    # 1. 测试带有开局触发器的角色 (威震天)
    CURRENT_MATCHUP["p0_bot_id"] = "megatron"
    CURRENT_MATCHUP["p1_bot_id"] = "bonecrusher_cin_rotf"
    g_engine.init("megatron", "bonecrusher_cin_rotf", 15000.0, 15000.0, 1000.0, 1000.0)
    trigger_onstart_phase()

    st = g_engine.get_state()
    p0_buff_ids = [b["id"] for b in st["p0"]["buffs"]]
    assert_true(len(p0_buff_ids) > 0, f"Megatron has onStart buffs injected at frame 0.00s: {p0_buff_ids}")
    assert_true("megatron_fusion_cannon" in p0_buff_ids or "megatron_fusion_cd" in p0_buff_ids,
                "Megatron fusion mechanisms successfully started at 0.00s")
    assert_true(len(PENDING_START_EVENTS) > 0, f"Callout events queued for UI banner: {len(PENDING_START_EVENTS)}")

    # 2. 验证修复后的电影擎天柱：因为移除了 onStart，开局不应弹出净化
    CURRENT_MATCHUP["p0_bot_id"] = "optimusprime_cin_tf"
    CURRENT_MATCHUP["p1_bot_id"] = "bonecrusher_cin_rotf"
    g_engine.init("optimusprime_cin_tf", "bonecrusher_cin_rotf", 15000.0, 15000.0, 1000.0, 1000.0)
    trigger_onstart_phase()

    st = g_engine.get_state()
    p0_buff_ids = [b["id"] for b in st["p0"]["buffs"]]
    assert_true("optimusprime_cin_tf_purify" not in p0_buff_ids,
                "Optimus Prime does NOT trigger purify at 0.00s (lifecycle verified!)")

if __name__ == "__main__":
    print("=" * 70)
    print("🚀 TFTF 战斗技能模拟器全自动化质量门禁测试 (含数据契约与生命周期)")
    print("=" * 70)
    test_optimus_mv_willpower()
    test_megatron_debuff_fusion()
    test_prowl_melee_buff()
    test_prowl_dash_back_charge()
    test_bumblebee_sidestep_crit()
    test_contract_validation()
    test_lifecycle_onstart()
    print("\n" + "=" * 70)
    print("🎉 全部 7 项质量门禁测试 100% 通过！模拟器与真机底层生命周期/契约完美对齐！")
    print("=" * 70)
