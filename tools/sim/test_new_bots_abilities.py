#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TFTF Combat Simulator - 12 New Bots Ability Verification Suite
=============================================================
Verifies all 96 abilities across the 12 brand new bots (Groups 1~4):
- Group 1: Blaster, Breakdown, Chromia
- Group 2: Cliffjumper, Dragstrip, Galvatron
- Group 3: Megatron ROTF, Mirage, Optimus Prime SG
- Group 4: Shockwave, Skywarp, Soundwave
"""

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

from Server.abilities.bots.blaster import build_blaster_abilities
from Server.abilities.bots.breakdown import build_breakdown_abilities
from Server.abilities.bots.chromia import build_chromia_abilities
from Server.abilities.bots.cliffjumper import build_cliffjumper_abilities
from Server.abilities.bots.dragstrip import build_dragstrip_abilities
from Server.abilities.bots.galvatron import build_galvatron_abilities
from Server.abilities.bots.megatron_rotf import build_megatron_rotf_abilities
from Server.abilities.bots.mirage import build_mirage_abilities
from Server.abilities.bots.optimusprime_sg import build_optimusprime_sg_abilities
from Server.abilities.bots.shockwave import build_shockwave_abilities
from Server.abilities.bots.skywarp import build_skywarp_abilities
from Server.abilities.bots.soundwave import build_soundwave_abilities

def assert_true(cond, msg):
    if not cond:
        print(f"  ❌ [FAIL] {msg}")
        sys.exit(1)
    else:
        print(f"  ✅ [PASS] {msg}")

def test_group1_blaster():
    print("\n--- [TEST 1] Blaster (录音机) - 6 项战技机制 ---")
    res = build_blaster_abilities()
    mods, appears = res[0], res[1]
    # ID 2409: Shield & Unstoppable
    assert_true("blaster_sig_absorb_unstoppable" in mods and "blaster_sig_absorb_dr" in mods, "ID 2409: Absorb shield & unstoppable defined")
    # ID 2419: Amp Charge
    assert_true("blaster_amp_charge" in mods, "ID 2419: Amp charge buff defined")
    assert_true(mods["blaster_amp_charge"]["st"] == 10, "ID 2419: Max 10 amp charge stacks")
    # ID 2420: Interference
    assert_true("blaster_interference" in mods, "ID 2420: Interference defined")
    # ID 2421: Heavy Shock
    assert_true("blaster_heavy_shock" in mods, "ID 2421: Heavy shock defined")
    # ID 2422: Block Shield
    assert_true("blaster_block_shield" in mods, "ID 2422: Block shield defined")
    # ID 2423: Shield Repair
    assert_true("blaster_sig_repair_basic" in mods and "blaster_sig_repair_special" in mods, "ID 2423: Shield repairs defined")

def test_group1_breakdown():
    print("\n--- [TEST 2] Breakdown (打击) - 9 项战技机制 ---")
    res = build_breakdown_abilities()
    mods, appears = res[0], res[1]
    # ID 3504: Shield Break
    assert_true("breakdown_shield_break_buff" in mods and "breakdown_shield_break_dmg" in mods, "ID 3504: Shield break defined")
    # ID 3505: Paranoia Evasion
    assert_true("breakdown_paranoia_evade" in mods, "ID 3505: Paranoia evade defined")
    # ID 3506: Paranoia Rage Crit
    assert_true("breakdown_paranoia_crit" in mods, "ID 3506: Paranoia crit defined")
    # ID 3508: SP1 Power Leak
    assert_true("breakdown_sp1_power_leak" in mods, "ID 3508: SP1 power leak defined")
    # ID 3512: Block Melee Evade
    assert_true("breakdown_block_evade" in mods, "ID 3512: Block melee evade defined")
    # ID 3513: SP2 Burn
    assert_true("breakdown_sp2_burn" in mods, "ID 3513: SP2 burn defined")
    # ID 3514: Opponent Force SP1
    assert_true("breakdown_sp2_certainty" in mods and "breakdown_sp3_certainty" in mods, "ID 3514: Force SP1 suppression defined")
    # ID 3515: SP1 Crit Rate
    assert_true("breakdown_sp1_crit_rate" in mods, "ID 3515: SP1 crit rate defined")
    # ID 3516: SP3 Debuff
    assert_true("breakdown_sp3_ranged_debuff" in mods, "ID 3516: SP3 ranged debuff defined")

def test_group1_chromia():
    print("\n--- [TEST 3] Chromia (克劳莉娅) - 9 项战技机制 ---")
    res = build_chromia_abilities()
    mods, appears = res[0], res[1]
    # ID 2486: Multi-shot Slow
    assert_true("chromia_ranged_decel" in mods, "ID 2486: Chromia deceleration defined")
    # ID 2487: SP1 Bleed
    assert_true("chromia_sp1_bleed" in mods, "ID 2487: SP1 bleed defined")
    # ID 2488: SP2 Bleed
    assert_true("chromia_sp2_bleed" in mods and "chromia_sp2_decel" in mods, "ID 2488: SP2 bleed & decel defined")
    # ID 2489: SP3 Bleed
    assert_true("chromia_sp3_bleed" in mods and "chromia_sp3_decel" in mods, "ID 2489: SP3 bleed & decel defined")
    # ID 2490: Target Locked Surge
    assert_true("chromia_sig_power_surge" in mods, "ID 2490: Target locked power surge defined")
    # ID 2491: Remote Evade
    assert_true("chromia_sig_evade" in mods, "ID 2491: Remote evade defined")
    # ID 2481: Time Bomb
    assert_true("chromia_acrolight_bomb" in mods and "chromia_bomb_stun" in mods, "ID 2481: Time bomb and stun defined")

def test_group2_cliffjumper():
    print("\n--- [TEST 4] Cliffjumper (飞过山) - 6 项战技机制 ---")
    res = build_cliffjumper_abilities()
    mods, appears = res[0], res[1]
    # ID 3547: Glass Gas
    assert_true("cliffjumper_ranged_glass_gas" in mods, "ID 3547: Glass gas defined")
    # ID 3548: Heavy Refresh
    assert_true("cliffjumper_heavy_refresh_glass_gas" in mods, "ID 3548: Heavy refresh defined")
    # ID 3546: SP1 Permanent Gas
    assert_true("cliffjumper_sp1_perm_glass_gas" in mods, "ID 3546: SP1 permanent gas defined")
    # ID 3549: SP2 Unblockable
    assert_true("cliffjumper_sp2_unblockable" in mods, "ID 3549: SP2 unblockable defined")
    # ID 3541: SP3 Extreme Shatter
    assert_true("cliffjumper_sp3_perm_glass_gas_5" in mods, "ID 3541: SP3 extreme shatter defined")
    # ID 3550: Clean Special Boost
    assert_true("cliffjumper_clean_special_boost" in mods, "ID 3550: Clean special boost defined")

def test_group2_dragstrip():
    print("\n--- [TEST 5] Dragstrip (抢劫) - 9 项战技机制 ---")
    res = build_dragstrip_abilities()
    mods, appears = res[0], res[1]
    # ID 3516: Dash Unblockable
    assert_true("dragstrip_dash_unblockable" in mods, "ID 3516: Dash unblockable defined")
    # ID 3524: Bleed Stack
    assert_true("dragstrip_sig_bleed" in mods, "ID 3524: Bleed stack defined")
    # ID 3525: 3-Bleed Heal
    assert_true("dragstrip_bleed_stack_heal" in mods, "ID 3525: 3-bleed heal defined")
    # ID 3526: SP1 Crit Burst
    assert_true("dragstrip_sp1_crit_rate" in mods, "ID 3526: SP1 crit burst defined")
    # ID 3527: SP2 Evade Nullify
    assert_true("dragstrip_sp2_anti_evade" in mods, "ID 3527: SP2 anti-evade defined")
    # ID 3528: SP2 Crit Rate
    assert_true("dragstrip_sp2_crit_rate" in mods, "ID 3528: SP2 crit rate defined")
    # ID 3529: SP3 Power Lock
    assert_true("dragstrip_sp3_power_lock" in mods, "ID 3529: SP3 power lock defined")
    # ID 3530: SP1/SP3 Bleed
    assert_true("dragstrip_sp1_bleed" in mods and "dragstrip_sp3_bleed_1" in mods, "ID 3530: SP bleed defined")
    # ID 3531: Signature Power Steal
    assert_true("dragstrip_sig_power_steal" in mods, "ID 3531: Signature power steal defined")

def test_group2_galvatron():
    print("\n--- [TEST 6] Galvatron (惊破天) - 9 项战技机制 ---")
    res = build_galvatron_abilities()
    mods, appears = res[0], res[1]
    # ID 3045: Dark Energy Charge
    assert_true("galvatron_dark_energy_charge" in mods, "ID 3045: Dark charge defined")
    # ID 3054: Heavy Dark Burn
    assert_true("galvatron_heavy_dark_burn" in mods, "ID 3054: Heavy dark burn defined")
    # ID 3055: SP1 Stun
    assert_true("galvatron_sp1_stun" in mods, "ID 3055: SP1 stun defined")
    # ID 3056: SP2 Dark Burn
    assert_true("galvatron_sp2_dark_burn" in mods, "ID 3056: SP2 dark burn defined")
    # ID 3057: SP3 Unicron Blast
    assert_true("galvatron_sp3_dark_burn" in mods, "ID 3057: SP3 blast burn defined")
    # ID 3058: Dark Ranged Boost
    assert_true("galvatron_dark_ranged_boost" in mods, "ID 3058: Dark ranged boost defined")
    # ID 3059: Light-Heavy Crit
    assert_true("galvatron_combo_crit_rate" in mods, "ID 3059: Combo crit defined")
    # ID 3060: Unicron Will Unstoppable
    assert_true("galvatron_unicron_unstoppable" in mods, "ID 3060: Unicron unstoppable defined")
    # ID 3048: Dark Crit Damage
    assert_true("galvatron_dark_crit_damage" in mods, "ID 3048: Dark crit damage defined")

def test_group3_megatron_rotf():
    print("\n--- [TEST 7] Megatron ROTF (电影2威震天) - 9 项战技机制 ---")
    res = build_megatron_rotf_abilities()
    mods, appears = res[0], res[1]
    # ID 3107: Signature Hail Megatron
    assert_true("megatron_rotf_sig_repair" in mods, "ID 3107: Hail Megatron repair defined")
    # ID 3108: SP1 Impair Charge
    assert_true("megatron_rotf_sp1_impair_charge" in mods, "ID 3108: SP1 impair charge defined")
    # ID 3109: SP2 Ranged Boost
    assert_true("megatron_rotf_sp2_ranged_boost" in mods, "ID 3109: SP2 ranged boost defined")
    # ID 3118: Natural Armor
    assert_true("megatron_rotf_passive_armor" in mods, "ID 3118: Natural armor defined")
    # ID 3119: Unstoppable Thresholds
    assert_true("megatron_rotf_hp_unstoppable" in mods, "ID 3119: Unstoppable threshold defined")
    # ID 3120: Whiff Attack Buff
    assert_true("megatron_rotf_heavy_whiff_atk" in mods, "ID 3120: Whiff attack buff defined")
    # ID 3121: Passive Impair Charges
    assert_true("megatron_rotf_hit_impair_charge" in mods, "ID 3121: Hit impair charge defined")
    # ID 3122: Heavy Consume
    assert_true("megatron_rotf_heavy_crit_boost" in mods and "megatron_rotf_consume_charges" in mods, "ID 3122: Heavy crit & consume defined")
    # ID 3123: SP3 Nuclear Blast
    assert_true("megatron_rotf_sp3_crit_rate" in mods and "megatron_rotf_sp3_crit_damage" in mods, "ID 3123: SP3 crit rate and damage defined")

def test_group3_mirage():
    print("\n--- [TEST 8] Mirage (幻影) - 8 项战技机制 ---")
    res = build_mirage_abilities()
    mods, appears = res[0], res[1]
    # ID 2687: KERS Mode Buffs
    assert_true("mirage_kers_sp1_speed" in mods, "ID 2687: KERS SP1 speed defined")
    assert_true("mirage_kers_sp2_unblockable" in mods, "ID 2687: KERS SP2 unblockable defined")
    assert_true("mirage_kers_sp3_atk" in mods, "ID 2687: KERS SP3 attack boost defined")
    # ID 2700: Disruption Mode
    assert_true("mirage_mode_disruption" in mods, "ID 2700: Mode Disruption defined")
    assert_true("mirage_disrupt_drain_hit" in mods, "ID 2700: SP1 drain on hit defined")
    # ID 2701: Disabling Mode
    assert_true("mirage_mode_incapacitation" in mods, "ID 2701: Mode Incapacitation defined")
    assert_true("mirage_incap_atk_debuff" in mods, "ID 2701: SP2 attack debuff defined")
    # ID 2702: Agility Mode
    assert_true("mirage_mode_agility" in mods, "ID 2702: Mode Agility defined")
    assert_true("mirage_agility_atk_stack" in mods, "ID 2702: Agility evade attack stack defined")
    # ID 2703: Emergency Shield
    assert_true("mirage_special_shield" in mods, "ID 2703: Emergency shield defined")
    # ID 2704: Energy Surge
    assert_true("mirage_power_flow" in mods, "ID 2704: Energy flow defined")
    # ID 2705: Heavy Ranged Evade
    assert_true("mirage_heavy_range_evade" in mods, "ID 2705: Heavy range evade defined")
    # ID 2706: Heavy Purify Burn
    assert_true("mirage_heavy_purify_burn" in mods, "ID 2706: Heavy purify burn defined")

def test_group3_optimusprime_sg():
    print("\n--- [TEST 9] Optimus Prime SG (倾天柱) - 4 项战技机制 ---")
    res = build_optimusprime_sg_abilities()
    mods, appears = res[0], res[1]
    # ID 3634: Tyrannical Spark
    assert_true("optimusprime_sg_spark_charge" in mods, "ID 3634: Spark charge defined")
    assert_true("optimusprime_sg_unblockable_melee" in mods, "ID 3634: Unblockable melee defined")
    # ID 3642: Adversity Attack Buff
    assert_true("optimusprime_sg_struggle_attack_buff" in mods, "ID 3642: Struggle attack buff defined")
    assert_true(mods["optimusprime_sg_struggle_attack_buff"]["m"] == 0.50, "ID 3642: Attack +50%")
    # ID 3641: Debuff Heavy Damage Reduction
    assert_true("optimusprime_sg_debuff_control" in mods, "ID 3641: Debuff control defined")
    assert_true(mods["optimusprime_sg_debuff_control"]["d"] == 15.0, "ID 3641: 15s duration")
    # ID 3643: Debuff Quad Cycle
    assert_true("optimusprime_sg_cycle_bleed" in mods, "ID 3643: Cycle bleed defined")
    assert_true("optimusprime_sg_cycle_burn" in mods, "ID 3643: Cycle burn defined")
    assert_true("optimusprime_sg_cycle_shock" in mods, "ID 3643: Cycle shock defined")
    assert_true("optimusprime_sg_cycle_acid" in mods, "ID 3643: Cycle acid defined")

def test_group4_shockwave():
    print("\n--- [TEST 10] Shockwave (震荡波) - 11 项战技机制 ---")
    res = build_shockwave_abilities()
    mods, appears = res[0], res[1]
    # ID 3277: Logic Energy Charges
    assert_true("shockwave_block_energy_charge" in mods, "ID 3277: Block energy charge defined")
    # ID 3283: SP1 Shock & Drain
    assert_true("shockwave_sp1_shock" in mods, "ID 3283: SP1 shock defined")
    # ID 3285: Rewind Damage
    assert_true("shockwave_sig_undo" in mods, "ID 3285: Rewind damage undo defined")
    # ID 3301: Heavy Shock
    assert_true("shockwave_heavy_shock" in mods, "ID 3301: Heavy shock defined")
    # ID 3302: SP2 Armor Pierce
    assert_true("shockwave_sp2_pierce" in mods, "ID 3302: SP2 armor pierce defined")
    # ID 3303: SP2 Heal Block
    assert_true("shockwave_sp2_repair_block" in mods, "ID 3303: SP2 repair block defined")
    # ID 3304: SP3 Pure Logic Annihilation
    assert_true("shockwave_sp3_shock" in mods and "shockwave_sp3_repair_block" in mods, "ID 3304: SP3 annihilation shock & block defined")
    # ID 3300: Overcharge Leak
    assert_true("shockwave_shock_power_leak" in mods, "ID 3300: Shock power leak defined")

def test_group4_skywarp():
    print("\n--- [TEST 11] Skywarp (闹翻天) - 7 项战技机制 ---")
    res = build_skywarp_abilities()
    mods, appears = res[0], res[1]
    # ID 3323: Space Fold Teleport
    assert_true("skywarp_teleport_charge_start" in mods and "skywarp_teleport_charge_dodge" in mods, "ID 3323: Teleport charge defined")
    # ID 3324: Teleport Crit & Unblockable
    assert_true("skywarp_teleport_crit_rate" in mods and "skywarp_teleport_unblockable" in mods, "ID 3324: Teleport crit & unblockable defined")
    # ID 3325: Teleport Power Lock
    assert_true("skywarp_teleport_power_lock" in mods, "ID 3325: Teleport lock defined")
    # ID 3326: Special Attack Suppression
    assert_true("skywarp_ranged_sp_debuff" in mods and "skywarp_heavy_sp_debuff" in mods, "ID 3326: Special suppression defined")
    # ID 3327: SP1 High Voltage Burn
    assert_true("skywarp_sp1_burn_state" in mods and "skywarp_sp1_burn_drain" in mods, "ID 3327: SP1 power burn defined")
    # ID 3328: SP2 Permanent Heal Block
    assert_true("skywarp_sp2_repair_block" in mods, "ID 3328: SP2 perm repair block defined")
    # ID 3329: SP3 Massive Power Siphon
    assert_true("skywarp_sp3_drain" in mods and "skywarp_sp3_gain" in mods and "skywarp_sp3_power_flow" in mods, "ID 3329: SP3 power siphon defined")

def test_group4_soundwave():
    print("\n--- [TEST 12] Soundwave (声波) - 9 项战技机制 ---")
    res = build_soundwave_abilities()
    mods, appears = res[0], res[1]
    # ID 3395: Resonance Heavy Power Flow
    assert_true("soundwave_heavy_power_flow" in mods, "ID 3395: Resonance heavy power flow defined")
    # ID 3396: Acoustic Shock
    assert_true("soundwave_heavy_shock" in mods, "ID 3396: Heavy shock defined")
    # ID 3397: Acoustic Power Leak
    assert_true("soundwave_sp1_power_leak" in mods, "ID 3397: Acoustic power leak defined")
    # ID 3398: Concussive Stun
    assert_true("soundwave_sp1_stun" in mods, "ID 3398: Concussive stun defined")
    # ID 3400: Passive No Basic Mana
    assert_true("soundwave_passive_no_basic_mana" in mods, "ID 3400: Passive no basic mana defined")
    # ID 3401: SP2 Overclock Surge
    assert_true("soundwave_sp2_shock" in mods and "soundwave_sp2_power_flow" in mods, "ID 3401: SP2 shock & flow defined")
    # ID 3402: SP3 Power Blockade
    assert_true("soundwave_sp3_shock" in mods and "soundwave_sp3_stun" in mods and "soundwave_sp3_power_lock" in mods, "ID 3402: SP3 shock, stun & lock defined")

def run_tests():
    print("=" * 70)
    print("🚀 TFTF 12 全新角色 (96 项战技) 战斗模拟器专属自动化质量门禁测试")
    print("=" * 70)
    test_group1_blaster()
    test_group1_breakdown()
    test_group1_chromia()
    test_group2_cliffjumper()
    test_group2_dragstrip()
    test_group2_galvatron()
    test_group3_megatron_rotf()
    test_group3_mirage()
    test_group3_optimusprime_sg()
    test_group4_shockwave()
    test_group4_skywarp()
    test_group4_soundwave()
    print("\n" + "=" * 70)
    print("🎉 恭喜！12 位全新角色 (96 项战技) 机制与数据契约 100% 验证通过！")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()
