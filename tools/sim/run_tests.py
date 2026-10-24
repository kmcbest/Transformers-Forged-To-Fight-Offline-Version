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


def test_windblade_abilities():
    print("\n--- [TEST 8] Windblade: Blade Crit, Resolution, Bleed, Stun & SP Mechanics ---")
    g_engine.init("windblade_gs", "bonecrusher_cin_rotf", 15000.0, 15000.0, 1000.0, 1000.0)
    g_engine.reset()

    # 1. 验证被动：重击远程穿透与规避
    # 风刃起手重击蓄力/飞行 (act=4)
    g_engine.attack_start(0, 4)
    st = g_engine.get_state()
    p0_buffs = [b["id"] for b in st["p0"]["buffs"]]
    assert_true("windblade_heavy_range_immune" in p0_buffs, "Windblade has windblade_heavy_range_immune active during heavy attack")

    # 对手向正在重击冲刺的风刃发起远程攻击 (act=8)，风刃处于重击姿态应 100% 穿透规避 (0 伤害)
    dmg_taken = g_engine.attack(1, 8, 0, 1, 0)
    assert_true(dmg_taken == 0, f"Windblade heavy attack 100% penetrated/evaded remote attack, dmg_taken={dmg_taken}")

    # 风刃重击命中对手并收招，穿透图标随之清除
    g_engine.attack(0, 4, 0, 1, 0)
    st_post_heavy = g_engine.get_state()
    p0_buffs_post = [b["id"] for b in st_post_heavy["p0"]["buffs"]]
    assert_true("windblade_heavy_range_immune" not in p0_buffs_post,
                "Windblade heavy attack connected and finished, windblade_heavy_range_immune cleanly consumed")

    # 2. 验证流血压制远程眩晕及敌方放S技时的【优先级门禁】
    # 先给对手施加流血
    g_engine.inject_buff(1, "dmg_bleed", 10.0, 1)

    # 2a. 门禁测试 A: 对手正在释放特殊技 (in_special=1)
    g_engine.set_special_attacking(1, True)
    # 风刃远程攻击打在放特殊技的对手身上，严禁打断或施加眩晕！
    for _ in range(6):
        g_engine.attack(0, 8, 0, 1, 0)
    st_special = g_engine.get_state()
    p1_buffs_special = [b["id"] for b in st_special["p1"]["buffs"]]
    assert_true("windblade_bleed_remote_stun" not in p1_buffs_special,
                "Priority Gate PASS: Ranged hit never interrupts or stuns opponent during their Special Attack!")
    g_engine.set_special_attacking(1, False)

    # 2b. 门禁测试 B: 对手未放特殊技，风刃远程攻击判定流血压制眩晕
    stun_triggered = False
    for _ in range(15):
        g_engine.attack(0, 8, 0, 1, 0)
        st = g_engine.get_state()
        p1_buffs = [b["id"] for b in st["p1"]["buffs"]]
        if "windblade_bleed_remote_stun" in p1_buffs:
            stun_triggered = True
            break
    assert_true(stun_triggered, "Windblade ranged attack stunned bleeding opponent (windblade_bleed_remote_stun applied)")

    # 3. 验证 SP1 能量驱散、多段 Hit 序列与【严格单层震击断言】
    # 给对手注入 2 层能量获取增益
    g_engine.inject_buff(1, "power_gain", 10.0, 2)
    st_before = g_engine.get_state()
    assert_true(any("power" in b["id"] for b in st_before["p1"]["buffs"]), "Opponent has power buff before SP1")

    # 3a. SP1 第一击 (Hit 0, is_last=0): 驱散能量增益，但严禁施加震击！
    g_engine.attack(0, 16, 0, 0, 0) # act=16, hit_idx=0, is_last=0
    st_hit0 = g_engine.get_state()
    p1_buffs_hit0 = {b["id"]: b["stacks"] for b in st_hit0["p1"]["buffs"]}
    assert_true(not any("power" in b for b in p1_buffs_hit0), "Opponent power buffs dispelled on SP1 first hit")
    assert_true("windblade_sp1_shock" not in p1_buffs_hit0, "SP1 Hit 0 (is_last=0) does NOT apply shock (multi-hit sequencing verified!)")

    # 3b. SP1 最后一击 (Hit 1, is_last=1): 施加且仅施加 1 层震击！
    g_engine.attack(0, 16, 1, 1, 0) # act=16, hit_idx=1, is_last=1
    st_hit1 = g_engine.get_state()
    p1_buffs_hit1 = {b["id"]: b["stacks"] for b in st_hit1["p1"]["buffs"]}
    assert_true("windblade_sp1_shock" in p1_buffs_hit1, "SP1 Stormfall Shock applied on last hit")
    assert_true(p1_buffs_hit1.get("windblade_sp1_shock", 0) == 1,
                f"Strict Stack Gate PASS: SP1 shock has EXACTLY 1 stack (actual: {p1_buffs_hit1.get('windblade_sp1_shock', 0)})")

    # 3c. 密集判定防刷机制: 模拟快速子命中 (rapid sub-hit), 震击依然保持 1 层
    g_engine.attack(0, 16, 1, 1, 0)
    st_debounce = g_engine.get_state()
    p1_buffs_deb = {b["id"]: b["stacks"] for b in st_debounce["p1"]["buffs"]}
    assert_true(p1_buffs_deb.get("windblade_sp1_shock", 0) == 1,
                "Debounce & Stack Clamp PASS: Rapid sub-hit still maintains strictly 1 stack of shock!")

    # 4. 验证 SP2 护甲穿透增益
    g_engine.attack(0, 32, 0, 1, 0) # SP2
    st_sp2 = g_engine.get_state()
    p0_buffs_sp2 = [b["id"] for b in st_sp2["p0"]["buffs"]]
    assert_true("windblade_sp2_armor_pierce" in p0_buffs_sp2, "Windblade gained 6s armor pierce (windblade_sp2_armor_pierce)")

    # 5. 验证数据契约有效性
    for mid in ["windblade_crit_bleed", "windblade_blade_crit_rate", "windblade_signature_resolution",
                "windblade_heavy_range_immune", "windblade_bleed_remote_stun", "windblade_sp1_power_nullify",
                "windblade_sp1_shock", "windblade_sp2_armor_pierce", "windblade_sp3_stun"]:
        dec = decorate_buff({"id": mid, "rem_ms": 3000, "stacks": 1})
        assert_true(dec["is_contract_valid"] == True, f"Contract valid for {mid}")
        assert_true(dec["name"] != mid, f"Decorated name exists for {mid}: {dec['name']}")
        assert_true(dec["pua"].startswith("0x"), f"PUA icon exists for {mid}: {dec['pua']}")

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
    test_windblade_abilities()
    print("\n" + "=" * 70)
    print("🎉 全部 8 项质量门禁测试 100% 通过！风刃全套专属机制与底层契约完美闭环！")
    print("=" * 70)
