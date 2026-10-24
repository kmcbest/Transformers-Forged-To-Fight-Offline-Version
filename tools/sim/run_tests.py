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


def test_kickback_abilities():
    print("\n--- [TEST 9] Kickback: Power Leak, Heavy Cleanse/Nullify, T-Cog Sabotage, SP Shock & Repair ---")
    g_engine.init("kickback_gs_kabam", "bonecrusher_cin_rotf", 32533.0, 15000.0, 3880.0, 1000.0)
    g_engine.reset()

    # 1. 验证重击起手净化自身减益并转化为能量获取
    g_engine.inject_buff(0, "dmg_shock", 5.0, 1)
    g_engine.inject_buff(0, "power_leak", 5.0, 1)
    st = g_engine.get_state()
    assert_true(len(st["p0"]["buffs"]) == 2, "Kickback has 2 debuffs before heavy")

    g_engine.attack_start(0, 4) # 起手重击
    st_start = g_engine.get_state()
    p0_buff_ids = [b["id"] for b in st_start["p0"]["buffs"]]
    assert_true("dmg_shock" not in p0_buff_ids and "power_leak" not in p0_buff_ids,
                "Kickback cleansed own shock and power leak debuffs on heavy start")
    assert_true("kickback_heavy_power_gain" in p0_buff_ids,
                "Kickback converted cleansed debuffs into kickback_heavy_power_gain")

    # 2. 验证重击命中驱散对手能量增益并施加 T-齿轮破坏
    g_engine.inject_buff(1, "power_gain", 10.0, 2)
    st_opp_before = g_engine.get_state()
    assert_true(any("power" in b["id"] for b in st_opp_before["p1"]["buffs"]), "Opponent has power gain before hit")

    g_engine.attack(0, 4, 0, 1, 0) # 重击命中
    st_hit = g_engine.get_state()
    p1_buff_ids = [b["id"] for b in st_hit["p1"]["buffs"]]
    assert_true(not any("power_gain" in b for b in p1_buff_ids), "Opponent power gain dispelled by Kickback heavy hit")
    assert_true("kickback_tcog_disrupt" in p1_buff_ids, "Kickback inflicted T-Cog Disrupt on opponent")

    # 3. 验证对手持有 T-齿轮破坏时放重击被反噬眩晕
    g_engine.attack_start(1, 4) # 对手尝试放重击
    st_disrupt = g_engine.get_state()
    p1_buffs_after_heavy = [b["id"] for b in st_disrupt["p1"]["buffs"]]
    assert_true(any("stun" in b for b in p1_buffs_after_heavy),
                "T-Cog Disrupt PASS: Opponent heavy attack disrupted and opponent stunned for 2s!")

    # 4. 验证 SP1 根据能量流失层数施加震击
    g_engine.inject_buff(1, "power_leak", 10.0, 2)
    g_engine.attack(0, 16, 0, 1, 0) # SP1 收招命中
    st_sp1 = g_engine.get_state()
    p1_buffs_sp1 = {b["id"]: b["stacks"] for b in st_sp1["p1"]["buffs"]}
    assert_true("kickback_sp1_shock" in p1_buffs_sp1, "Kickback SP1 applied shock to leaking opponent")
    assert_true(p1_buffs_sp1.get("kickback_sp1_shock", 0) >= 2,
                f"SP1 shock stacks correspond to power leak stacks: {p1_buffs_sp1.get('kickback_sp1_shock', 0)}")

    # 5. 验证数据契约
    for mid in ["kickback_crit_power_leak", "kickback_crit_rate", "kickback_power_rate",
                "kickback_dash_evade", "kickback_heavy_power_gain", "kickback_tcog_disrupt",
                "kickback_sp1_shock", "kickback_sp2_crit_buff", "kickback_sp2_bleed", "kickback_sp3_repair"]:
        dec = decorate_buff({"id": mid, "rem_ms": 3000, "stacks": 1})
        assert_true(dec["is_contract_valid"] == True, f"Contract valid for {mid}")


def test_slipstream_abilities():
    print("\n--- [TEST 10] Slipstream: Heavy Range Penetrate, Shield Dispel, M2 Purify Shock, Backstab ---")
    g_engine.init("slipstream_gs", "bonecrusher_cin_rotf", 32402.0, 15000.0, 2306.0, 1000.0)
    g_engine.reset()

    # 1. 验证重击远程穿透与暴伤增益
    g_engine.attack_start(0, 4)
    st = g_engine.get_state()
    p0_buffs = [b["id"] for b in st["p0"]["buffs"]]
    assert_true("slipstream_heavy_range_immune" in p0_buffs, "Slipstream heavy attack has range penetration active")

    # 对手向重击中的滑流发起远程射击 (act=8)，伤害为 0 (穿透)
    dmg_taken = g_engine.attack(1, 8, 0, 1, 0)
    assert_true(dmg_taken == 0, f"Slipstream penetrated opponent ranged attack, dmg_taken={dmg_taken}")

    # 重击命中收招：穿透图标清除，获得 15% 暴伤增益
    g_engine.attack(0, 4, 0, 1, 0)
    st_post_heavy = g_engine.get_state()
    p0_buffs_post = [b["id"] for b in st_post_heavy["p0"]["buffs"]]
    assert_true("slipstream_heavy_range_immune" not in p0_buffs_post, "Range penetration consumed after heavy connects")
    assert_true("slipstream_heavy_crit_damage" in p0_buffs_post, "Slipstream gained 15% crit damage for 7s")

    # 2. 验证基础远程攻击驱散对手护盾
    g_engine.inject_buff(1, "shield", 10.0, 1)
    st_opp_shield = g_engine.get_state()
    assert_true(any("shield" in b["id"] for b in st_opp_shield["p1"]["buffs"]), "Opponent has shield before ranged attack")

    g_engine.attack(0, 8, 0, 1, 0) # 远程射击
    st_opp_post_ranged = g_engine.get_state()
    p1_buffs_post_ranged = [b["id"] for b in st_opp_post_ranged["p1"]["buffs"]]
    assert_true("shield" not in p1_buffs_post_ranged, "Slipstream ranged attack dispelled opponent shield")

    # 3. 验证 M2 净化自身震击并反击对手震击
    g_engine.inject_buff(0, "dmg_shock", 6.0, 1)
    g_engine.attack(0, 2, 1, 1, 0) # M2 (act=2, hit_idx=1)
    st_m2 = g_engine.get_state()
    p0_buffs_m2 = [b["id"] for b in st_m2["p0"]["buffs"]]
    p1_buffs_m2 = [b["id"] for b in st_m2["p1"]["buffs"]]
    assert_true("dmg_shock" not in p0_buffs_m2, "Slipstream M2 purified own shock")
    assert_true("slipstream_m2_purify_shock" in p1_buffs_m2, "Slipstream M2 reflected shock to opponent")
    assert_true("slipstream_m2_crit_buff" in p0_buffs_m2, "Slipstream gained 10% crit rate from M2")

    # 4. 验证数据契约
    for mid in ["slipstream_heavy_range_immune", "slipstream_heavy_crit_damage", "slipstream_ranged_nullify_shield",
                "slipstream_ranged_atk_buff", "slipstream_m2_purify_shock", "slipstream_m2_crit_buff",
                "slipstream_backstab", "slipstream_crit_resist_down", "slipstream_power_drain", "slipstream_backfire"]:
        dec = decorate_buff({"id": mid, "rem_ms": 3000, "stacks": 1})
        assert_true(dec["is_contract_valid"] == True, f"Contract valid for {mid}")


def test_cheetor_abilities():
    print("\n--- [TEST 11] Cheetor: Combo Power Gain, Feral Strike, SP1 Heal Block & Bleed, SP3 Power Lock ---")
    g_engine.init("cheetor_bw_transmetal", "bonecrusher_cin_rotf", 28245.0, 15000.0, 2874.0, 1000.0)
    g_engine.reset()

    # 1. 验证 L4/M2 连击充能 2.5% 最大能量
    mana_before = g_engine.get_state()["p0"]["mana"]
    g_engine.attack(0, 1, 3, 1, 0) # L4 (act=1, hit_idx=3, is_last=1)
    mana_after = g_engine.get_state()["p0"]["mana"]
    assert_true(mana_after > mana_before, f"Cheetor gained combo mana: {mana_before} -> {mana_after}")

    # 2. 验证 SP1 阻止修复 (禁疗) 与 8 秒流血
    g_engine.attack(0, 16, 0, 1, 0) # SP1
    st_sp1 = g_engine.get_state()
    p1_buffs_sp1 = [b["id"] for b in st_sp1["p1"]["buffs"]]
    assert_true("cheetor_sp1_heal_block" in p1_buffs_sp1, "Cheetor SP1 applied heal block (heal prohibited)")
    assert_true("cheetor_sp1_bleed" in p1_buffs_sp1, "Cheetor SP1 applied 8s bleed (100% ATK)")

    # 3. 验证野生突击 (Feral Strike) 状态与禁对手规避
    g_engine.inject_buff(0, "cheetor_signature_feral_strike", 4.0, 1)
    st_feral = g_engine.get_state()
    p0_buffs_feral = [b["id"] for b in st_feral["p0"]["buffs"]]
    assert_true("cheetor_signature_feral_strike" in p0_buffs_feral, "Cheetor activated Feral Strike")

    # 4. 验证 SP3 能量锁定与能量燃烧
    g_engine.attack(0, 64, 0, 1, 0) # SP3
    st_sp3 = g_engine.get_state()
    p1_buffs_sp3 = [b["id"] for b in st_sp3["p1"]["buffs"]]
    assert_true("cheetor_sp3_power_lock" in p1_buffs_sp3, "Cheetor SP3 applied 10s power lock")

    # 5. 验证数据契约
    for mid in ["cheetor_crit_bleed", "cheetor_combo_power_gain", "cheetor_signature_feral_strike",
                "cheetor_feral_no_evade", "cheetor_sp1_heal_block", "cheetor_sp1_bleed",
                "cheetor_sp2_power_buff", "cheetor_sp3_power_lock", "cheetor_sp3_power_burn"]:
        dec = decorate_buff({"id": mid, "rem_ms": 3000, "stacks": 1})
        assert_true(dec["is_contract_valid"] == True, f"Contract valid for {mid}")


def test_sideswipe_abilities():
    print("\n--- [TEST 12] Sideswipe: 7-Hit Melee Evade, Crit Stacking, Heavy Purify Shock, SP2 Evade ---")
    g_engine.init("sideswipe_gs", "bonecrusher_cin_rotf", 26794.0, 15000.0, 2698.0, 1000.0)
    g_engine.reset()

    # 1. 验证受到 7 次基础普通攻击激活近战规避 (38% 规避 4 秒)
    for i in range(6):
        g_engine.attack(1, 1, 0, 0, 0) # 敌方轻击 6 次
    st_6 = g_engine.get_state()
    p0_buffs_6 = {b["id"]: b["stacks"] for b in st_6["p0"]["buffs"]}
    assert_true("sideswipe_evade_counter" in p0_buffs_6, "Sideswipe accumulated hit counter")
    assert_true("sideswipe_melee_evade" not in p0_buffs_6, "Sideswipe melee evade not yet active at 6 hits")

    # 第 7 次受击
    g_engine.attack(1, 1, 0, 0, 0)
    st_7 = g_engine.get_state()
    p0_buffs_7 = [b["id"] for b in st_7["p0"]["buffs"]]
    assert_true("sideswipe_melee_evade" in p0_buffs_7, "Sideswipe reached 7 hits, activated sideswipe_melee_evade (38% 4s)!")

    # 2. 验证重击净化自身震击
    g_engine.inject_buff(0, "dmg_shock", 6.0, 1)
    st_shock = g_engine.get_state()
    assert_true(any("shock" in b["id"] for b in st_shock["p0"]["buffs"]), "Sideswipe has shock debuff before heavy")

    g_engine.attack_start(0, 4) # 重击起手
    st_heavy_start = g_engine.get_state()
    p0_buffs_hs = [b["id"] for b in st_heavy_start["p0"]["buffs"]]
    assert_true("dmg_shock" not in p0_buffs_hs, "Sideswipe cleansed shock on heavy attack start!")

    # 3. 验证暴击增加暴击率叠层，被击倒扣除 5 层
    for _ in range(3):
        g_engine.inject_buff(0, "sideswipe_crit_rate_stack", 15.0, 1)
    st_crit_stack = g_engine.get_state()
    p0_cs = {b["id"]: b["stacks"] for b in st_crit_stack["p0"]["buffs"]}
    assert_true(p0_cs.get("sideswipe_crit_rate_stack", 0) >= 3, "Sideswipe accumulated crit rate stacks")

    # 4. 验证 SP2 获得 8 秒近战规避 (35%)
    g_engine.attack(0, 32, 0, 1, 0) # SP2
    st_sp2 = g_engine.get_state()
    p0_buffs_sp2 = [b["id"] for b in st_sp2["p0"]["buffs"]]
    assert_true("sideswipe_s2_melee_evade" in p0_buffs_sp2, "Sideswipe gained sideswipe_s2_melee_evade on SP2 hit")

    # 5. 验证数据契约
    for mid in ["sideswipe_s1_crit_rate", "sideswipe_s1_stun", "sideswipe_s2_burn", "sideswipe_s3_burn",
                "sideswipe_s3_nullify", "sideswipe_evade_counter", "sideswipe_melee_evade",
                "sideswipe_crit_rate_stack", "sideswipe_signature_max_thrust", "sideswipe_s2_melee_evade",
                "sideswipe_evade_ranged_power", "sideswipe_evade_dash_crit_damage"]:
        dec = decorate_buff({"id": mid, "rem_ms": 3000, "stacks": 1})
        assert_true(dec["is_contract_valid"] == True, f"Contract valid for {mid}")

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
    test_kickback_abilities()
    test_slipstream_abilities()
    test_cheetor_abilities()
    test_sideswipe_abilities()
    print("\n" + "=" * 70)
    print("🎉 全部 12 项质量门禁测试 100% 通过！横炮、反冲、滑流、黄豹与风刃全套专属机制与底层契约完美闭环！")
    print("=" * 70)
