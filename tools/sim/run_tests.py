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
    print("\n--- [TEST 3] Prowl: Melee-Only Damage Scaling (Strictly Exclude Ranged & Specials) ---")
    g_engine.init("prowl_gs_deluxe2016", "bonecrusher_cin_rotf", 15000.0, 15000.0, 1000.0, 1000.0)
    g_engine.reset()

    # 1. 无增益基础伤害
    base_melee_dmg = g_engine.attack(0, 1, 0, 0, 0)  # 轻击近战: 1000 * 0.25 = 250
    base_ranged_dmg = g_engine.attack(0, 8, 0, 0, 0) # 远程射击: 1000 * 0.35 = 350
    base_sp1_dmg = g_engine.attack(0, 16, 0, 0, 0)   # 特殊技1: 1000 * 1.80 = 1800

    # 2. 注入 10 层近战增益 (prowl_melee_buff)
    g_engine.inject_buff(0, "prowl_melee_buff", 6.0, 10)
    boosted_melee_dmg = g_engine.attack(0, 1, 0, 0, 0)
    boosted_ranged_dmg = g_engine.attack(0, 8, 0, 0, 0)
    boosted_sp1_dmg = g_engine.attack(0, 16, 0, 0, 0)

    # 验证：仅近战攻击获得 110% 加成 (250 * 2.10 = 525)
    assert_true(boosted_melee_dmg > base_melee_dmg, f"Melee damage boosted ({boosted_melee_dmg} > {base_melee_dmg})")
    assert_true(abs(boosted_melee_dmg - base_melee_dmg * 2.10) < 1.0, f"Melee damage matches exact +110% (+11%/stack): {boosted_melee_dmg} == {base_melee_dmg * 2.10}")

    # 验证：远程射击与特殊技绝不享受近战增益！
    assert_true(abs(boosted_ranged_dmg - base_ranged_dmg) < 0.1, f"Ranged attack NOT boosted by melee buff (strictly melee-only): {boosted_ranged_dmg} == {base_ranged_dmg}")
    assert_true(abs(boosted_sp1_dmg - base_sp1_dmg) < 0.1, f"Special attack NOT boosted by melee buff (strictly melee-only): {boosted_sp1_dmg} == {base_sp1_dmg}")

def test_prowl_dash_back_charge():
    print("\n--- [TEST 4] Prowl: Dash Back Charge & Strict Interrupt Quality Gates ---")
    g_engine.init("prowl_gs_deluxe2016", "bonecrusher_cin_rotf", 15000.0, 15000.0, 1000.0, 1000.0)
    g_engine.reset()

    # --- 1. 后闪开始充能 (图标应为灰色拳头 E412) ---
    g_engine.dodge(0, 0)
    st = g_engine.get_state()
    p0_buffs = {b["id"]: b for b in st["p0"]["buffs"]}
    assert_true("prowl_melee_charge" in p0_buffs, "Prowl started charging with prowl_melee_charge")
    assert_true(p0_buffs["prowl_melee_charge"]["stacks"] == 1, "Initial charge is 1 stack")

    # 递增时间至 4 层
    for _ in range(15):
        g_engine.tick(100)
    st = g_engine.get_state()
    stacks = {b["id"]: b["stacks"] for b in st["p0"]["buffs"]}["prowl_melee_charge"]
    assert_true(stacks >= 4, f"Charge stacks increased with time (expected >=4, actual {stacks})")

    # --- 2. 远程射击测试：远程开枪不应打断充能 ---
    g_engine.attack(0, 8, 0, 0, 0) # 远程射击
    st = g_engine.get_state()
    p0_buffs = {b["id"]: b for b in st["p0"]["buffs"]}
    assert_true("prowl_melee_charge" in p0_buffs, "Remote shooting does NOT interrupt charging!")

    # --- 3. 打断门禁1：近战打中对手，打断充能并转化为对应层数近战增益 ---
    g_engine.attack(0, 1, 0, 0, 0) # 近战轻击命中
    st = g_engine.get_state()
    p0_buffs = {b["id"]: b for b in st["p0"]["buffs"]}
    assert_true("prowl_melee_charge" not in p0_buffs, "Interrupt 1 PASS: Charging buff cleared when melee attack hit opponent")
    assert_true("prowl_melee_buff" in p0_buffs, "Interrupt 1 PASS: Converted to orange prowl_melee_buff")

    # --- 4. 打断门禁2：主动前冲，打断充能 ---
    g_engine.reset()
    g_engine.dodge(0, 0) # 再次后闪充能
    g_engine.tick(600)   # 充到2层
    assert_true("prowl_melee_charge" in {b["id"]: b for b in g_engine.get_state()["p0"]["buffs"]}, "Prowl recharged after dodge")
    g_engine.dash(0)     # 主动前冲
    p0_buffs = {b["id"]: b for b in g_engine.get_state()["p0"]["buffs"]}
    assert_true("prowl_melee_charge" not in p0_buffs, "Interrupt 2 PASS: Active Dash forward immediately interrupted charge!")
    assert_true("prowl_melee_buff" in p0_buffs, "Interrupt 2 PASS: Converted to prowl_melee_buff on dash interrupt")

    # --- 5. 打断门禁3：放S技，无论打没打中，都打断 ---
    g_engine.reset()
    g_engine.dodge(0, 0) # 再次后闪充能
    g_engine.tick(600)   # 充到2层
    assert_true("prowl_melee_charge" in {b["id"]: b for b in g_engine.get_state()["p0"]["buffs"]}, "Prowl recharged after dodge")
    g_engine.attack_start(0, 16) # 释放SP1起手 (尚未判定任何命中)
    p0_buffs = {b["id"]: b for b in g_engine.get_state()["p0"]["buffs"]}
    assert_true("prowl_melee_charge" not in p0_buffs, "Interrupt 3 PASS: Activating Special Attack immediately interrupted charge (regardless of hit)!")
    assert_true("prowl_melee_buff" in p0_buffs, "Interrupt 3 PASS: Converted to prowl_melee_buff on special attack start")

    # --- 6. 矢量图标契约门禁：检查充能与近战增益 PUA 均为 E412 (拳头图标) ---
    c_charge = decorate_buff({"id": "prowl_melee_charge", "stacks": 1, "rem_ms": 6000})
    assert_true(c_charge.get("pua") == "0xE412", f"prowl_melee_charge PUA icon is 0xE412 (fist), got: {c_charge.get('pua')}")
    c_buff = decorate_buff({"id": "prowl_passive_melee_buff", "stacks": 1, "rem_ms": 6000})
    assert_true(c_buff.get("pua") == "0xE412", f"prowl_passive_melee_buff PUA icon is 0xE412 (fist), got: {c_buff.get('pua')}")

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

    # 5. 验证数据契约与官方真理源 PUA 图标绑定
    expected_kickback_puas = {
        "kickback_tcog_disrupt": "0xE60F",
        "kickback_power_rate": "0xE606",
        "kickback_heavy_power_gain": "0xE606",
        "kickback_sp1_shock": "0xE914",
        "kickback_sp2_bleed": "0xE401",
    }
    for mid in ["kickback_crit_power_leak", "kickback_crit_rate", "kickback_power_rate",
                "kickback_dash_evade", "kickback_heavy_power_gain", "kickback_tcog_disrupt",
                "kickback_sp1_shock", "kickback_sp2_crit_buff", "kickback_sp2_bleed", "kickback_sp3_repair"]:
        dec = decorate_buff({"id": mid, "rem_ms": 3000, "stacks": 1})
        assert_true(dec["is_contract_valid"] == True, f"Contract valid for {mid}")
        if mid in expected_kickback_puas:
            assert_true(dec.get("pua") == expected_kickback_puas[mid],
                        f"{mid} PUA icon mismatch: expected {expected_kickback_puas[mid]}, got {dec.get('pua')}")


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

    # 4. 验证数据契约与官方真理源 PUA 图标绑定
    expected_slipstream_puas = {
        "slipstream_heavy_crit_damage": "0xE906",
        "slipstream_m2_purify_shock": "0xE914",
        "slipstream_backstab": "0xE41E",
        "slipstream_backfire": "0xE901",
    }
    for mid in ["slipstream_heavy_range_immune", "slipstream_heavy_crit_damage", "slipstream_ranged_nullify_shield",
                "slipstream_ranged_atk_buff", "slipstream_m2_purify_shock", "slipstream_m2_crit_buff",
                "slipstream_backstab", "slipstream_crit_resist_down", "slipstream_power_drain", "slipstream_backfire"]:
        dec = decorate_buff({"id": mid, "rem_ms": 3000, "stacks": 1})
        assert_true(dec["is_contract_valid"] == True, f"Contract valid for {mid}")
        if mid in expected_slipstream_puas:
            assert_true(dec.get("pua") == expected_slipstream_puas[mid],
                        f"{mid} PUA icon mismatch: expected {expected_slipstream_puas[mid]}, got {dec.get('pua')}")

    # 3b. 验证 M2 单按 (hit=1, is_last=1) 与 5连击末尾 (hit=4, is_last=1) 均能稳定触发，且 L2 (hit=1, act=1) 绝不误触发 M2
    g_engine.reset()
    # 模拟 5 连击前段：L1, L2, L3
    g_engine.attack(0, 1, 0, 0, 0) # L1
    g_engine.attack(0, 1, 1, 0, 0) # L2 (act=1, hit=1)
    st_l2 = g_engine.get_state()
    assert_true("slipstream_m2_crit_buff" not in [b["id"] for b in st_l2["p0"]["buffs"]], "L2 (hit=1, act=1) must NOT trigger M2 crit buff")
    g_engine.attack(0, 1, 2, 0, 0) # L3
    g_engine.attack(0, 2, 3, 0, 0) # M1 (act=2, hit=3, last=0)
    assert_true("slipstream_m2_crit_buff" not in [b["id"] for b in g_engine.get_state()["p0"]["buffs"]], "M1 must NOT trigger M2 crit buff")
    g_engine.attack(0, 2, 4, 1, 0) # M2 (act=2, hit=4, last=1)
    st_combo_m2 = g_engine.get_state()
    assert_true("slipstream_m2_crit_buff" in [b["id"] for b in st_combo_m2["p0"]["buffs"]], "Combo M2 (hit=4, last=1) successfully triggered M2 crit buff")

    # 3c. 验证 M2 震击单层约束 (严禁溢出堆叠为 x2 或 x3)
    g_engine.inject_buff(1, "slipstream_m2_purify_shock", 4.0, 1)
    g_engine.inject_buff(1, "slipstream_m2_purify_shock", 8.0, 1)
    shock_buff = next(b for b in g_engine.get_state()["p1"]["buffs"] if b["id"] == "slipstream_m2_purify_shock")
    assert_true(shock_buff["stacks"] == 1, f"slipstream_m2_purify_shock strictly clamped to 1 stack (got {shock_buff['stacks']})")

    # 5. [门禁1] 利用弱点：对方无减益时不ROLL、不刷新
    g_engine.init("slipstream_gs", "prowl", 32402.0, 15000.0, 2306.0, 1000.0)
    g_engine.reset()
    st0 = g_engine.get_state()
    assert_true(len(st0["p1"]["buffs"]) == 0, "Opponent has 0 debuffs initially")
    g_engine.attack(0, 1, 0, 1, 0) # 轻击
    st1 = g_engine.get_state()
    assert_true(len(st1["p1"]["buffs"]) == 0, "Exploit Weakness: No roll when opponent has 0 debuffs")

    # 5b. [门禁1b] 利用弱点：当对方拥有 3 个减益时，掷骰命中只能随机刷新其中 1 个减益持续时间，另外 2 个保持原持续时间！
    g_engine.reset()
    g_engine.inject_buff(1, "slipstream_crit_resist_down", 2.0, 1)
    g_engine.inject_buff(1, "slipstream_power_drain", 2.0, 1)
    g_engine.inject_buff(1, "slipstream_backfire", 2.0, 1)
    # 轻击多次直至触发利用弱点
    for _ in range(20):
        g_engine.attack(0, 1, 0, 1, 0)
        st_exp = g_engine.get_state()
        p1_buffs_exp = st_exp["p1"]["buffs"]
        refreshed_count = sum(1 for b in p1_buffs_exp if b["rem_ms"] > 4000)
        if refreshed_count > 0:
            assert_true(refreshed_count == 1, f"Exploit Weakness strictly refreshed EXACTLY 1 debuff, not all 3! (refreshed={refreshed_count})")
            for b in p1_buffs_exp:
                assert_true(b["stacks"] == 1, f"Debuff {b['id']} stacks remain strictly 1, no duplicate stacking!")
            break

    # 6. [门禁2] 暴击触发背刺：先施加灰色 E41E 图标 (0.5s)，到期后消失并转化为三态减益之一
    g_engine.reset()
    g_engine.set_crit_rate(0, 1.0) # 强制暴击
    for _ in range(20):
        g_engine.attack(0, 1, 0, 1, 0)
        st_crit = g_engine.get_state()
        if "slipstream_backstab" in [b["id"] for b in st_crit["p1"]["buffs"]]:
            break
    p1_buffs_crit = [b["id"] for b in g_engine.get_state()["p1"]["buffs"]]
    assert_true("slipstream_backstab" in p1_buffs_crit, "Backstab triggered: opponent received slipstream_backstab (gray icon)")
    bs_buff = next(b for b in g_engine.get_state()["p1"]["buffs"] if b["id"] == "slipstream_backstab")
    assert_true(bs_buff["rem_ms"] <= 500, f"slipstream_backstab duration is 0.5s, got rem_ms={bs_buff['rem_ms']}")
    assert_true(bs_buff["stacks"] == 1, "slipstream_backstab is strictly 1 stack")

    # 推进时间 0.55s (550ms)，触发背刺到期转化
    g_engine.tick(550)
    st_post_bs = g_engine.get_state()
    p1_buffs_post_bs = [b["id"] for b in st_post_bs["p1"]["buffs"]]
    assert_true("slipstream_backstab" not in p1_buffs_post_bs, "slipstream_backstab gray icon expired and removed after 0.5s")
    
    valid_debuffs = ["slipstream_crit_resist_down", "slipstream_power_drain", "slipstream_backfire"]
    applied_bs_debuffs = [b for b in st_post_bs["p1"]["buffs"] if b["id"] in valid_debuffs]
    assert_true(len(applied_bs_debuffs) == 1, f"Backstab resolved into exactly 1 of 3 debuffs: {[b['id'] for b in applied_bs_debuffs]}")
    assert_true(applied_bs_debuffs[0]["stacks"] == 1, f"Resolved debuff strictly clamped to 1 stack: {applied_bs_debuffs[0]['stacks']}")

    # 7. [门禁4] 背刺减益层数严格为1，并遵循流转规则：
    # （三个减益都最大只能叠1层。如果已有某个减益，则随机在另两个中间选，如果已有两个，则必然变成第三个，如果三个都有，则刷新随机到的那个）
    first_debuff_id = applied_bs_debuffs[0]["id"]
    remaining_2 = [d for d in valid_debuffs if d != first_debuff_id]
    second_debuff_id = remaining_2[0]
    third_debuff_id = remaining_2[1]
    g_engine.inject_buff(1, second_debuff_id, 8.0, 1)

    # 此时对手已有两个减益，再次触发背刺 (60%几率) 并推进0.55s -> 必然转化为第三个减益！
    for _ in range(20):
        g_engine.attack(0, 1, 0, 1, 0)
        st_try = g_engine.get_state()
        if "slipstream_backstab" in [b["id"] for b in st_try["p1"]["buffs"]]:
            break
    assert_true("slipstream_backstab" in [b["id"] for b in g_engine.get_state()["p1"]["buffs"]], "Backstab triggered with 2 debuffs present")
    g_engine.tick(550)
    st_all_3 = g_engine.get_state()
    p1_all_buff_ids = [b["id"] for b in st_all_3["p1"]["buffs"]]
    assert_true(third_debuff_id in p1_all_buff_ids, f"Backstab strictly resolved into the 3rd missing debuff: {third_debuff_id}")
    for b in st_all_3["p1"]["buffs"]:
        if b["id"] in valid_debuffs:
            assert_true(b["stacks"] == 1, f"Debuff {b['id']} strictly has max 1 stack (got {b['stacks']})")

    # 8. [门禁3] 逆火反噬机制：有逆火减益的角色，放SP技会受到逆火反噬伤害并消除逆火；重击绝不触发逆火
    g_engine.reset()
    g_engine.inject_buff(1, "slipstream_backfire", 8.0, 1)

    # 8a. 门禁验证：对手出重击 (act=4 / act=0x100) 绝对不扣逆火反噬血，逆火减益绝不被消耗！且对手绝不获得滑流远程穿透！
    hp_before_heavy = g_engine.get_state()["p1"]["hp"]
    g_engine.attack_start(1, 4)
    g_engine.attack_start(1, 0x100)
    hp_after_heavy = g_engine.get_state()["p1"]["hp"]
    assert_true(hp_after_heavy == hp_before_heavy, "Opponent Heavy Attack does NOT trigger Backfire backlash damage")
    assert_true("slipstream_backfire" in [b["id"] for b in g_engine.get_state()["p1"]["buffs"]], "Backfire remains active after heavy attack")
    assert_true("slipstream_heavy_range_immune" not in [b["id"] for b in g_engine.get_state()["p1"]["buffs"]], "Opponent does NOT receive Slipstream Heavy Range Penetration")

    # 8b. 对手释放 SP 技 (act=16)：受到滑流 100% 攻击力伤害并消耗逆火减益
    g_engine.attack_start(1, 16)
    hp_after_sp = g_engine.get_state()["p1"]["hp"]
    dmg_taken_bf = hp_after_heavy - hp_after_sp
    assert_true(abs(dmg_taken_bf - (2306.0 * 1.0)) < 1.0, f"Slipstream Backfire backlash damage matches 100% ATK: {dmg_taken_bf} == {2306.0 * 1.0}")
    p1_buffs_after_sp = [b["id"] for b in g_engine.get_state()["p1"]["buffs"]]
    assert_true("slipstream_backfire" not in p1_buffs_after_sp, "slipstream_backfire consumed upon casting SP")

    # 巨蝎勇士 (Scorponok) 逆火反噬机制验证：反噬承受巨蝎 153% 攻击力伤害 (3000 * 1.53 = 4590.0)
    g_engine.inject_buff(1, "scorponok_venom_backfire", 8.0, 1)
    hp_before_sp_sc = g_engine.get_state()["p1"]["hp"]
    g_engine.attack_start(1, 16)
    hp_after_sp_sc = g_engine.get_state()["p1"]["hp"]
    dmg_taken_bf_sc = hp_before_sp_sc - hp_after_sp_sc
    assert_true(abs(dmg_taken_bf_sc - (3000.0 * 1.53)) < 1.0, f"Scorponok Backfire backlash damage matches 153% ATK: {dmg_taken_bf_sc} == {3000.0 * 1.53}")
    p1_buffs_after_sp_sc = [b["id"] for b in g_engine.get_state()["p1"]["buffs"]]
    assert_true("scorponok_venom_backfire" not in p1_buffs_after_sp_sc, "scorponok_venom_backfire consumed upon casting SP")


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

    # 3. 验证获得一格能量自动激活野生突击 (Feral Strike) 状态与禁对手规避
    g_engine.set_mana(0, 1.0)
    g_engine.tick(100) # 驱动 simulation tick
    st_feral = g_engine.get_state()
    p0_buffs_feral = [b["id"] for b in st_feral["p0"]["buffs"]]
    p1_buffs_feral = [b["id"] for b in st_feral["p1"]["buffs"]]
    assert_true("cheetor_signature_feral_strike" in p0_buffs_feral, "Cheetor automatically activated Feral Strike upon filling 1 bar of power")
    assert_true("cheetor_feral_no_evade" in p1_buffs_feral, "Opponent received feral_no_evade upon Cheetor Feral Strike")

    # 3b. 门禁验证：黄豹能量守护 (免疫能量流失与能量燃烧)
    g_engine.inject_buff(0, "power_leak", 10.0, 1)
    g_engine.inject_buff(0, "power_drain", 10.0, 1)
    st_imm = g_engine.get_state()
    p0_buffs_imm = [b["id"] for b in st_imm["p0"]["buffs"]]
    assert_true("power_leak" not in p0_buffs_imm, "Cheetor is immune to power_leak (gated)")
    assert_true("power_drain" not in p0_buffs_imm, "Cheetor is immune to power_drain (gated)")

    # 4. 验证 SP3 能量锁定与能量燃烧
    g_engine.attack(0, 64, 0, 1, 0) # SP3
    st_sp3 = g_engine.get_state()
    p1_buffs_sp3 = [b["id"] for b in st_sp3["p1"]["buffs"]]
    assert_true("cheetor_sp3_power_lock" in p1_buffs_sp3, "Cheetor SP3 applied 10s power lock")

    # 5. 验证数据契约与官方真理源 PUA 图标绑定
    expected_cheetor_puas = {
        "cheetor_signature_feral_strike": "0xE160",
        "cheetor_combo_power_gain": "0xE608",
        "cheetor_sp1_heal_block": "0xE90C",
        "cheetor_sp2_power_buff": "0xE608",
        "cheetor_sp3_power_lock": "0xE523",
    }
    for mid in ["cheetor_crit_bleed", "cheetor_combo_power_gain", "cheetor_signature_feral_strike",
                "cheetor_feral_no_evade", "cheetor_sp1_heal_block", "cheetor_sp1_bleed",
                "cheetor_sp2_power_buff", "cheetor_sp3_power_lock", "cheetor_sp3_power_burn"]:
        dec = decorate_buff({"id": mid, "rem_ms": 3000, "stacks": 1})
        assert_true(dec["is_contract_valid"] == True, f"Contract valid for {mid}")
        if mid in expected_cheetor_puas:
            assert_true(dec.get("pua") == expected_cheetor_puas[mid],
                        f"{mid} PUA icon mismatch: expected {expected_cheetor_puas[mid]}, got {dec.get('pua')}")


def test_sideswipe_abilities():
    print("\n--- [TEST 12] Sideswipe: 7-Hit Melee Evade, Crit Stacking, Heavy Purify Shock, SP2 Evade ---")
    g_engine.init("sideswipe_gs", "bonecrusher_cin_rotf", 26794.0, 15000.0, 2698.0, 1000.0)
    g_engine.reset()

    # 1. 验证受到 7 次基础普通攻击激活近战规避 (38% 规避 4 秒)
    # 并且验证 sideswipe_evade_counter 计数器随每次受击严格累加 (1..6 层)，绝不卡死在1层
    for i in range(6):
        g_engine.attack(1, 1, 0, 0, 0) # 敌方轻击 6 次
    st_6 = g_engine.get_state()
    p0_buffs_6 = {b["id"]: b["stacks"] for b in st_6["p0"]["buffs"]}
    assert_true("sideswipe_evade_counter" in p0_buffs_6, "Sideswipe accumulated hit counter")
    assert_true(p0_buffs_6["sideswipe_evade_counter"] == 6, f"Sideswipe evade counter strictly stacked to 6 (got {p0_buffs_6['sideswipe_evade_counter']})")
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

    # 4. 验证 S1 命中绝不获得规避 Buff，唯有 S2 命中才获得 8 秒近战规避 (35%)
    # 4a. S1 命中测试：确保不误触发任何规避增益 (sideswipe_melee_evade / sideswipe_s2_melee_evade)
    g_engine.reset()
    g_engine.attack(0, 16, 0, 1, 0) # S1 (special_index=1)
    st_s1 = g_engine.get_state()
    p0_buffs_s1 = [b["id"] for b in st_s1["p0"]["buffs"]]
    assert_true("sideswipe_melee_evade" not in p0_buffs_s1, "Sideswipe S1 hit strictly does NOT grant sideswipe_melee_evade")
    assert_true("sideswipe_s2_melee_evade" not in p0_buffs_s1, "Sideswipe S1 hit strictly does NOT grant sideswipe_s2_melee_evade")

    # 4b. S2 命中测试：正确获得 8 秒近战规避 (35%)
    g_engine.attack(0, 32, 0, 1, 0) # S2 (special_index=2)
    st_sp2 = g_engine.get_state()
    p0_buffs_sp2 = [b["id"] for b in st_sp2["p0"]["buffs"]]
    assert_true("sideswipe_s2_melee_evade" in p0_buffs_sp2, "Sideswipe gained sideswipe_s2_melee_evade on SP2 hit")

    # 4b. 验证远程闪避精准门禁 (空放/闪避近战绝不给能量；唯有闪避远程子弹时才获得13%能量与无伤化解)
    g_engine.reset()
    mana_before = g_engine.get_state()["p0"]["mana"]
    # 4b-1. 空放侧闪/后退：严禁增加能量，严禁激活 sideswipe_evade_ranged_power 或 sideswipe_evade_dash_crit_damage
    g_engine.dodge(0, 1) # 侧闪
    st_empty = g_engine.get_state()
    assert_true("sideswipe_evade_ranged_power" not in [b["id"] for b in st_empty["p0"]["buffs"]], "Empty dodge strictly does NOT trigger evade power buff")
    assert_true("sideswipe_evade_dash_crit_damage" not in [b["id"] for b in st_empty["p0"]["buffs"]], "Empty dodge strictly does NOT trigger dash crit damage buff")
    assert_true(st_empty["p0"]["mana"] == mana_before, "Empty dodge strictly does NOT grant mana")

    # 4b-1b. 闪避对方冲锋攻击 (Dash Attack)：精准获得 +108% 暴击伤害 (持续 6 秒)
    g_engine.reset()
    g_engine.dodge(0, 1) # 我方侧闪
    g_engine.attack(1, 32, 0, 1, 0) # 对方冲锋攻击 (Action.Dash)
    st_dash_evade = g_engine.get_state()
    assert_true("sideswipe_evade_dash_crit_damage" in [b["id"] for b in st_dash_evade["p0"]["buffs"]], "Sideswipe gained +108% crit damage on evading dash attack")

    # 4b-2. 验证闪避远程射击门禁与回能机制：
    # 场景A: 主动闪避无敌帧——我方侧闪，对方开枪被无伤规避，精准获得13%能量(+0.39格)与1秒能量增益
    g_engine.reset()
    mana_start = g_engine.get_state()["p0"]["mana"]
    g_engine.dodge(0, 1) # 我方侧闪
    g_engine.attack(1, 8, 0, 1, 0) # 对方远程开枪，直接被闪避
    st_active_evade = g_engine.get_state()
    assert_true(st_active_evade["p0"]["hp"] == 26794.0, "Active dodge fully evaded ranged bullet with 0 damage")
    assert_true("sideswipe_evade_ranged_power" in [b["id"] for b in st_active_evade["p0"]["buffs"]], "Sideswipe gained sideswipe_evade_ranged_power on evading remote shot")
    assert_true(abs(st_active_evade["p0"]["mana"] - (mana_start + 0.39)) < 0.01, f"Sideswipe gained exact 13% power (+0.39), got {st_active_evade['p0']['mana']:.2f}")

    # 场景B: 响应式闪避回退——对方先开枪，我方紧接着侧闪，伤害全数回退化解无伤
    g_engine.reset()
    g_engine.attack(1, 8, 0, 1, 0) # 对方远程射击
    assert_true(g_engine.get_state()["p0"]["hp"] < 26794.0, "Shot dealt damage initially before reactive dodge")
    g_engine.dodge(0, 1) # 我方迅速侧闪化解子弹
    st_reactive = g_engine.get_state()
    assert_true(st_reactive["p0"]["hp"] == 26794.0, "Reactive dodge fully refunded/evaded ranged bullet damage")
    assert_true("sideswipe_evade_ranged_power" in [b["id"] for b in st_reactive["p0"]["buffs"]], "Sideswipe gained sideswipe_evade_ranged_power on reactive dodge")

    # 5. 验证数据契约与官方真理源 PUA 图标绑定
    expected_sideswipe_puas = {
        "sideswipe_signature_max_thrust": "0xE606",
        "sideswipe_evade_ranged_power": "0xE608",
        "sideswipe_evade_dash_crit_damage": "0xE906",
    }
    for mid in ["sideswipe_s1_crit_rate", "sideswipe_s1_stun", "sideswipe_s2_burn", "sideswipe_s3_burn",
                "sideswipe_s3_nullify", "sideswipe_evade_counter", "sideswipe_melee_evade",
                "sideswipe_crit_rate_stack", "sideswipe_signature_max_thrust", "sideswipe_s2_melee_evade",
                "sideswipe_evade_ranged_power", "sideswipe_evade_dash_crit_damage"]:
        dec = decorate_buff({"id": mid, "rem_ms": 3000, "stacks": 1})
        assert_true(dec["is_contract_valid"] == True, f"Contract valid for {mid}")
        if mid in expected_sideswipe_puas:
            assert_true(dec.get("pua") == expected_sideswipe_puas[mid],
                        f"{mid} PUA icon mismatch: expected {expected_sideswipe_puas[mid]}, got {dec.get('pua')}")

def test_necrotronus_abilities():
    print("\n--- [TEST 13] Necrotronus: Titan Charges, Overwhelming Power & Bleed, Power Debuff, SP Consumption ---")
    g_engine.init("necrotronus_gs_kabam", "bonecrusher_cin_rotf", 35484.0, 15000.0, 2519.0, 1000.0)
    g_engine.reset()

    # 0. 门禁验证：0.00s 开局绝不提前触发势不可挡、能量压制或觉醒愤怒
    st_init = g_engine.get_state()
    p0_init_buffs = [b["id"] for b in st_init["p0"]["buffs"]]
    p1_init_buffs = [b["id"] for b in st_init["p1"]["buffs"]]
    assert_true("necrotronus_overwhelming_power" not in p0_init_buffs, "Necrotronus does NOT trigger Overwhelming Power at 0.00s")
    assert_true("necrotronus_power_rate_debuff" not in p1_init_buffs, "Opponent does NOT receive power rate debuff at 0.00s")
    assert_true("necrotronus_signature_outrage" not in p0_init_buffs, "Necrotronus does NOT trigger Outrage buff at 0.00s")

    # 1. 验证普通攻击命中获得泰坦充能
    for i in range(5):
        g_engine.attack(0, 1, i, 0, 0)
    st = g_engine.get_state()
    p0_tc = next((b for b in st["p0"]["buffs"] if b["id"] == "necrotronus_titan_charge"), None)
    assert_true(p0_tc is not None and p0_tc["stacks"] == 5, f"Necrotronus accumulated 5 Titan Charges (got {p0_tc['stacks'] if p0_tc else 0})")

    # 1b. 门禁验证：攻击被对方格挡防御 (is_blocked = 1) 绝对不增加泰坦充能
    g_engine.attack(0, 1, 0, 0, 1) # 被防御
    st_blk = g_engine.get_state()
    p0_tc_blk = next((b for b in st_blk["p0"]["buffs"] if b["id"] == "necrotronus_titan_charge"), None)
    assert_true(p0_tc_blk["stacks"] == 5, f"Blocked attack does NOT grant Titan Charge (expected 5, got {p0_tc_blk['stacks']})")

    # 2. 累积至 20 层激活势不可挡模式 (红色E91A)
    for i in range(15):
        g_engine.attack(0, 1, i, 0, 0)
    st_20 = g_engine.get_state()
    p0_buffs_20 = [b["id"] for b in st_20["p0"]["buffs"]]
    assert_true("necrotronus_overwhelming_power" in p0_buffs_20, "Necrotronus reached 20 charges and entered Overwhelming Power")

    # 3. 势不可挡模式下，攻击 100% 施加 6 秒流血；被防御的攻击绝对不施加流血
    g_engine.attack(0, 1, 0, 1, 0) # 命中
    st_bleed = g_engine.get_state()
    p1_bleed = next((b for b in st_bleed["p1"]["buffs"] if b["id"] == "necrotronus_overwhelming_bleed"), None)
    assert_true(p1_bleed is not None, "Overwhelming Power applied 6s bleed on hit")
    assert_true(p1_bleed["stacks"] == 1, "Overwhelming Bleed is strictly 1 stack (refreshed)")

    # 3b. 门禁验证：势不可挡模式下，被格挡防御的攻击绝对不施加流血
    g_engine.tick(7000) # 先等待前一个流血到期
    assert_true("necrotronus_overwhelming_bleed" not in [b["id"] for b in g_engine.get_state()["p1"]["buffs"]], "Previous bleed expired")
    g_engine.attack(0, 1, 0, 1, 1) # 被防御
    assert_true("necrotronus_overwhelming_bleed" not in [b["id"] for b in g_engine.get_state()["p1"]["buffs"]], "Blocked attack in Overwhelming Power does NOT inflict bleed")

    # 4. 验证能量压制机制：对手能量高于亡灵天尊时施加 -30% 功率减益 (红标E606)，能量少于等于时自动消除
    g_engine.set_mana(0, 0.5)
    g_engine.set_mana(1, 1.5)
    g_engine.tick(100)
    st_mana_high = g_engine.get_state()
    p1_buffs_mh = [b["id"] for b in st_mana_high["p1"]["buffs"]]
    assert_true("necrotronus_power_rate_debuff" in p1_buffs_mh, "Opponent received power rate debuff when opponent mana > Necrotronus mana")

    g_engine.set_mana(0, 2.0)
    g_engine.tick(100)
    st_mana_low = g_engine.get_state()
    p1_buffs_ml = [b["id"] for b in st_mana_low["p1"]["buffs"]]
    assert_true("necrotronus_power_rate_debuff" not in p1_buffs_ml, "Power rate debuff removed when opponent mana <= Necrotronus mana")

    # 5. 验证 SP 消耗泰坦充能：SP1 消耗 10 层，充能由 20 降至 10 -> 势不可挡模式解除
    st_before_sp1 = g_engine.get_state()
    tc_before = next((b["stacks"] for b in st_before_sp1["p0"]["buffs"] if b["id"] == "necrotronus_titan_charge"), 0)
    assert_true(tc_before >= 20, f"Necrotronus has >=20 charges before SP1 (got {tc_before})")

    g_engine.attack(0, 16, 0, 1, 0) # SP1 (hit 0)
    st_after_sp1 = g_engine.get_state()
    tc_after = next((b["stacks"] for b in st_after_sp1["p0"]["buffs"] if b["id"] == "necrotronus_titan_charge"), 0)
    assert_true(tc_after == tc_before - 10, f"SP1 consumed 10 charges and does NOT gain charges on hit (actual: {tc_after})")
    assert_true("necrotronus_overwhelming_power" not in [b["id"] for b in st_after_sp1["p0"]["buffs"]], "Overwhelming Power cleanly exited when charges dropped below 20")

    # SP1 多段后续攻击同样绝不增加充能
    g_engine.attack(0, 16, 1, 1, 0) # SP1 (hit 1)
    tc_after_hit2 = next((b["stacks"] for b in g_engine.get_state()["p0"]["buffs"] if b["id"] == "necrotronus_titan_charge"), 0)
    assert_true(tc_after_hit2 == tc_after, f"SP multi-hits do not add Titan Charges: {tc_after_hit2} == {tc_after}")

    # 6. 验证霸体机制归属方：
    # 6a. 亡灵天尊自己放 SP 时，绝对不会触发预判霸体（双方均不应得到）
    g_engine.attack_start(0, 16) # 我方亡灵天尊释放 SP1
    assert_true("necrotronus_unstoppable" not in [b["id"] for b in g_engine.get_state()["p0"]["buffs"]], "Necrotronus does NOT gain unstoppable on self SP start")
    assert_true("necrotronus_unstoppable" not in [b["id"] for b in g_engine.get_state()["p1"]["buffs"]], "Opponent does NOT gain unstoppable on Necrotronus SP start")

    # 6b. 对方发动 SP 技时，我方亡灵天尊有 30% 几率获得 0.95 秒不可阻挡霸体
    unstoppable_triggered = False
    for _ in range(30):
        g_engine.attack_start(1, 16) # 对方释放 SP1
        if "necrotronus_unstoppable" in [b["id"] for b in g_engine.get_state()["p0"]["buffs"]]:
            unstoppable_triggered = True
            break
    assert_true(unstoppable_triggered, "Necrotronus gained unstoppable on opponent SP start")

    # 6c. 对方发动普通前冲 (Dash / Action 2) 时，绝对不触发亡灵天尊霸体判定
    # 先等待之前 SP 触发的 0.95s 霸体到期
    g_engine.tick(2000)
    for _ in range(30):
        g_engine.attack_start(1, 2) # 对方前冲 (Dash)
        assert_true("necrotronus_unstoppable" not in [b["id"] for b in g_engine.get_state()["p0"]["buffs"]], "Opponent Dash does NOT trigger Necrotronus unstoppable")

    # 7. 验证数据契约与官方真理源 PUA 图标绑定
    expected_necrotronus_puas = {
        "necrotronus_titan_charge": "0xE91A",
        "necrotronus_overwhelming_power": "0xE91A",
        "necrotronus_overwhelming_bleed": "0xE401",
        "necrotronus_power_rate_debuff": "0xE606",
        "necrotronus_unstoppable": "0xE915",
        "necrotronus_heavy_crit_rate": "0xE40D",
        "necrotronus_sp1_power_rate": "0xE606",
        "necrotronus_sp2_crit_buff": "0xE40D",
        "necrotronus_sp3_bleed": "0xE401",
        "necrotronus_signature_outrage": "0xE906",
    }
    for mid, exp_pua in expected_necrotronus_puas.items():
        dec = decorate_buff({"id": mid, "rem_ms": 3000, "stacks": 1})
        assert_true(dec["is_contract_valid"] == True, f"Contract valid for {mid}")
        assert_true(dec.get("pua") == exp_pua, f"{mid} PUA mismatch: expected {exp_pua}, got {dec.get('pua')}")



def test_wheeljack_abilities():
    print("\n--- [TEST 15] Wheeljack: SP1/SP2/SP3 Triple Debuffs (Shock, Leak, Stun) & Power Drain Tick ---")
    g_engine.init("wheeljack_gs_mp20", "bonecrusher_cin_rotf", 32402.0, 15000.0, 2306.0, 1000.0)
    g_engine.reset()

    # 1. 验证千斤顶 SP1 命中最终击施加减益 (Shock / Leak / Stun)
    # 给敌方设置 1 格能量，以便观察能量流失扣减；循环以消除单元测试中三率皆未命中的随机波动 (18% 几率)
    has_debuff = False
    p1_buffs = []
    for _ in range(10):
        g_engine.reset()
        g_engine.set_mana(1, 1.0)
        g_engine.attack(0, 16, 0, 1, 0) # SP1 last hit
        st_sp1 = g_engine.get_state()
        p1_buffs = [b["id"] for b in st_sp1["p1"]["buffs"]]
        if any(b in p1_buffs for b in ["wheeljack_sp1_shock", "wheeljack_sp1_leak", "wheeljack_sp1_stun", "power_leak", "dmg_shock"]):
            has_debuff = True
            break
    assert_true(has_debuff, f"Wheeljack SP1 successfully applied debuffs to target: {p1_buffs}")

    # 2. 验证能量流失在模拟器中随时间平滑扣减能量槽
    g_engine.inject_buff(1, "power_leak", 3.0, 1)
    mana_before = g_engine.get_state()["p1"]["mana"]
    g_engine.tick(1000) # tick 1 秒
    mana_after = g_engine.get_state()["p1"]["mana"]
    assert_true(mana_after < mana_before, f"Power leak smoothly drained target mana in simulator: {mana_before:.2f} -> {mana_after:.2f}")


def test_motormaster_abilities():
    print("\n--- [TEST 16] Motormaster: Dash & SP2 Unstoppable Gates ---")
    g_engine.init("motormaster_gs_voyager2015", "bonecrusher_cin_rotf", 34894.0, 15000.0, 2629.0, 1000.0)
    g_engine.reset()

    # 1. 验证前冲获得 0.7 秒不可阻挡霸体
    g_engine.dash(0)
    st_dash = g_engine.get_state()
    p0_buffs_dash = [b["id"] for b in st_dash["p0"]["buffs"]]
    assert_true("motormaster_dash_unstoppable" in p0_buffs_dash, "Motormaster gained unstoppable on Dash")

    # 2. 验证 SP2 获得 4.0 秒不可阻挡霸体
    g_engine.attack_start(0, 32) # SP2 start
    st_sp2 = g_engine.get_state()
    p0_buffs_sp2 = [b["id"] for b in st_sp2["p0"]["buffs"]]
    assert_true("motormaster_sp2_unstoppable" in p0_buffs_sp2, "Motormaster gained 4.0s unstoppable on SP2 start")


def test_player_invincible():
    print("\n--- [TEST 14] Launcher Setting: Player Invincibility Gate (受击不掉血) ---")
    g_engine.init("optimusprime_cin_tf", "megatron_gs_leader2015", 30000.0, 30000.0, 2000.0, 2000.0)
    g_engine.reset()

    # 1. 正常状态：敌方攻击我方，我方正常扣血
    st_init = g_engine.get_state()
    p0_init_hp = st_init["p0"]["hp"]
    g_engine.attack(1, 1, 0, 1, 0) # 敌方轻攻击第一击
    st_hit1 = g_engine.get_state()
    p0_hit1_hp = st_hit1["p0"]["hp"]
    assert_true(p0_hit1_hp < p0_init_hp, f"Normal combat: P0 takes damage when attacked (HP: {p0_init_hp} -> {p0_hit1_hp})")

    # 2. 开启玩家无敌：敌方攻击我方，我方 0 扣血 (HP 完全不减)
    g_engine.set_player_invincible(True)
    curr_hp = p0_hit1_hp
    for act in [1, 2, 4, 16, 32]: # 敌方连续打轻击、中击、重击、SP1、SP2
        g_engine.attack(1, act, 0, 1, 0)
        st = g_engine.get_state()
        assert_true(st["p0"]["hp"] == curr_hp, f"Player Invincible ON: P0 HP unchanged during enemy action {act} (HP: {st['p0']['hp']})")

    # 3. 验证单向有效性：我方攻击敌方，敌方依然正常扣血，丝毫不受影响
    p1_before = g_engine.get_state()["p1"]["hp"]
    g_engine.attack(0, 1, 0, 1, 0)
    p1_after = g_engine.get_state()["p1"]["hp"]
    assert_true(p1_after < p1_before, f"Player Invincible ON: Enemy P1 still takes full damage (HP: {p1_before} -> {p1_after})")

    # 4. 关闭玩家无敌：敌方再次攻击，恢复正常掉血
    g_engine.set_player_invincible(False)
    before_off = g_engine.get_state()["p0"]["hp"]
    g_engine.attack(1, 1, 0, 1, 0)
    after_off = g_engine.get_state()["p0"]["hp"]
    assert_true(after_off < before_off, f"Player Invincible OFF: P0 normal damage restored (HP: {before_off} -> {after_off})")



def test_block_state_enter():
    print("\n--- [TEST 18] Block State Lifecycle & Armor Damage Reduction ---")
    g_engine.init("optimusprime_cin_tf", "generic_enemy", 30000.0, 30000.0, 2500.0, 2500.0)
    g_engine.set_crit_rate(0, 0.0)
    g_engine.set_crit_rate(1, 0.0)
    g_engine.reset()

    # 进入格挡触发 onPlayerStateEnter (state=Block) -> optimusprime_cin_tf_block_armor
    g_engine.set_block(0, 1)
    st = g_engine.get_state()
    buffs = [b["id"] for b in st["p0"]["buffs"]]
    assert "optimusprime_cin_tf_block_armor" in buffs, "Optimus Prime block armor not triggered"
    print("  [PASS] Movie Optimus gained 7.0s block armor on block toggle")

    # 验证受击享受 16.5% 减伤 (2500 * 0.4 = 1000 -> 835.0)
    hp_before = st["p0"]["hp"]
    g_engine.attack(1, 2, 0, 1, 0)
    dmg = hp_before - g_engine.get_state()["p0"]["hp"]
    assert abs(dmg - 835.0) < 1.0, f"Expected 835.0, got {dmg}"
    print("  [PASS] Movie Optimus reduced damage by 16.5% under armor (1000 -> 835)")

    # G1 擎天柱
    g_engine.init("fte_optimus_gs_t3", "generic_enemy", 30000.0, 30000.0, 2500.0, 2500.0)
    g_engine.set_crit_rate(0, 0.0)
    g_engine.set_crit_rate(1, 0.0)
    g_engine.reset()
    g_engine.set_block(0, 1)
    buffs_g1 = [b["id"] for b in g_engine.get_state()["p0"]["buffs"]]
    assert "optimus_block_armor" in buffs_g1, "G1 Optimus block armor not triggered"
    print("  [PASS] G1 Optimus gained 2.5s block armor on block toggle")
    hp_g1 = g_engine.get_state()["p0"]["hp"]
    g_engine.attack(1, 2, 0, 1, 0)
    dmg_g1 = hp_g1 - g_engine.get_state()["p0"]["hp"]
    assert abs(dmg_g1 - 835.0) < 1.0, f"Expected 835.0, got {dmg_g1}"
    print("  [PASS] G1 Optimus reduced damage by 16.5% under armor (1000 -> 835)")

def test_projectile_speed_boost():
    print("\n--- [TEST 17] Projectile Flight Speed Quality Gate (Prowl SP2, Arcee SP1, Megatron Fusion Cannon) ---")

    # 1. 警车 (Prowl): SP2 激活前弹速 10.0，激活后弹速 15.0 (+50%)
    g_engine.init("prowl", "bonecrusher", 30000.0, 30000.0, 1000.0, 1000.0)
    g_engine.reset()
    spd_before = g_engine.get_projectile_speed(0, 10.0, is_heavy=False)
    assert_true(abs(spd_before - 10.0) < 1e-4, f"Prowl base projectile speed is 10.0: got {spd_before}")

    # 激活 SP2 (prowl_s2_ranged_boost)
    g_engine.inject_buff(0, "prowl_s2_ranged_boost", 6.0, 1)
    spd_sp2 = g_engine.get_projectile_speed(0, 10.0, is_heavy=False)
    assert_true(abs(spd_sp2 - 15.0) < 1e-4, f"Prowl SP2 boosted projectile speed by +50% (10.0 -> 15.0): got {spd_sp2}")

    # 2. 阿尔茜 (Arcee): SP1 激活前弹速 10.0，激活后弹速 14.0 (+40%)
    g_engine.init("arcee", "bonecrusher", 30000.0, 30000.0, 1000.0, 1000.0)
    g_engine.reset()
    spd_arcee_before = g_engine.get_projectile_speed(0, 10.0, is_heavy=False)
    assert_true(abs(spd_arcee_before - 10.0) < 1e-4, f"Arcee base projectile speed is 10.0: got {spd_arcee_before}")

    # 激活 SP1 (arcee_sp1_trick_shot)
    g_engine.inject_buff(0, "arcee_sp1_trick_shot", 6.5, 1)
    spd_arcee_sp1 = g_engine.get_projectile_speed(0, 10.0, is_heavy=False)
    assert_true(abs(spd_arcee_sp1 - 14.0) < 1e-4, f"Arcee SP1 boosted projectile speed by +40% (10.0 -> 14.0): got {spd_arcee_sp1}")

    # 3. 威震天 (Megatron Leader):
    # a) 无融合炮时，重击弹速 10.0 (未提速)
    g_engine.init("megatron", "bonecrusher", 30000.0, 30000.0, 1000.0, 1000.0)
    g_engine.reset()
    spd_mega_no_fusion = g_engine.get_projectile_speed(0, 10.0, is_heavy=True)
    assert_true(abs(spd_mega_no_fusion - 10.0) < 1e-4, f"Megatron heavy without fusion is unboosted (10.0): got {spd_mega_no_fusion}")

    # b) 拥有融合炮充能 (megatron_fusion_cannon) 时，重击飞行速度 +50% (10.0 -> 15.0)
    g_engine.inject_buff(0, "megatron_fusion_cannon", -1.0, 1)
    spd_mega_heavy = g_engine.get_projectile_speed(0, 10.0, is_heavy=True)
    assert_true(abs(spd_mega_heavy - 15.0) < 1e-4, f"Megatron heavy with fusion cannon boosted by +50% (10.0 -> 15.0): got {spd_mega_heavy}")

    # c) 拥有融合炮时，普通小枪远程攻击并不提速 (保持 10.0)
    spd_mega_ranged = g_engine.get_projectile_speed(0, 10.0, is_heavy=False)
    assert_true(abs(spd_mega_ranged - 10.0) < 1e-4, f"Megatron normal ranged attack is NOT boosted by fusion (10.0): got {spd_mega_ranged}")

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
    test_necrotronus_abilities()
    test_player_invincible()
    test_wheeljack_abilities()
    test_motormaster_abilities()
    test_projectile_speed_boost()
    test_block_state_enter()
    
    # --- [TEST 19] 震天尊 (Megatronus) 全套战斗机制与自主充能 ---
    from tools.sim.test_megatronus import run_tests as test_megatronus_suite
    test_megatronus_suite()

    print("\n" + "=" * 70)
    print("🎉 全部 19 项质量门禁测试 100% 通过！震天尊、子弹弹速提速、千斤顶、汽车大师等全角色机制闭环！")
    print("=" * 70)
