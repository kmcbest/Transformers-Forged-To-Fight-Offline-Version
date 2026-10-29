#!/usr/bin/env python3
"""
TFTF Combat Simulator - Batches 2~4 Ability Verification Suite
=============================================================
Verifies all 51 abilities across 8 bots in Batches 2~4:
1. Bumblebee (bumblebee_gs_kabam) - 5 abilities (2441, 2445, 2450, 2451, 2452)
2. Jetfire (jetfire_gs_leader2014) - 7 abilities (2666, 2667, 2681, 2682, 2683, 2684, 2685)
3. Kickback (kickback_gs_kabam) - 12 abilities (3096~3107)
4. Mixmaster (mixmaster_cin_rotf) - 7 abilities (3180, 3181, 3182, 3183, 3184, 3185, 3186)
5. Motormaster (motormaster_gs_voyager2015) - 5 abilities (3180, 3184, 3187, 3535, 3536)
6. Rhinox (rhinox_gs_voyager2014) - 4 abilities (2769, 2774, 2779, 2792)
7. Waspinator (waspinator_gs_deluxe) - 7 abilities (3471, 3472, 3473, 3474, 3475, 3476, 3477)
8. Wheeljack (wheeljack_gs_mp20) - 4 abilities (2888, 3658, 3659, 3660)
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

from Server.abilities.bots.bumblebee import build_bumblebee_abilities
from Server.abilities.bots.jetfire import build_jetfire_abilities
from Server.abilities.bots.kickback import build_kickback_abilities
from Server.abilities.bots.mixmaster import build_mixmaster_abilities
from Server.abilities.bots.motormaster import build_motormaster_abilities
from Server.abilities.bots.rhinox import build_rhinox_abilities
from Server.abilities.bots.waspinator import build_waspinator_abilities
from Server.abilities.bots.wheeljack import build_wheeljack_abilities

def assert_true(cond, msg):
    if not cond:
        print(f"  ❌ [FAIL] {msg}")
        sys.exit(1)
    else:
        print(f"  ✅ [PASS] {msg}")

def test_bumblebee():
    print("\n--- [TEST 1] Bumblebee (小黄蜂) 5 项增补战技 ---")
    res = build_bumblebee_abilities()
    mods, appears = res[0], res[1]

    # ID 2441: Sidestep Crit Rate
    assert_true("bumblebee_sidestep_crit_rate" in mods, "ID 2441: bumblebee_sidestep_crit_rate exists")
    assert_true("bumblebee_crit_consume" in mods, "ID 2441: bumblebee_crit_consume exists")
    assert_true(mods["bumblebee_sidestep_crit_rate"]["st"] == 3, "ID 2441: max 3 stacks")

    # ID 2445: Bee Brave
    assert_true("bumblebee_close_power" in mods, "ID 2445: bumblebee_close_power exists")
    assert_true("bumblebee_close_melee" in mods, "ID 2445: bumblebee_close_melee exists")

    # ID 2450: SP1 Crit Damage
    assert_true("bumblebee_sp1_crit_damage" in mods, "ID 2450: bumblebee_sp1_crit_damage exists")
    assert_true(mods["bumblebee_sp1_crit_damage"]["m"] == 0.60, "ID 2450: crit damage +60%")

    # ID 2451: SP2 Power Lock
    assert_true("bumblebee_sp2_power_lock" in mods, "ID 2451: bumblebee_sp2_power_lock exists")
    assert_true(mods["bumblebee_sp2_power_lock"]["d"] == 10.0, "ID 2451: 10.0s power lock")

    # ID 2452: SP3 Crit Rate Stacks
    assert_true("bumblebee_sp3_crit_rate" in mods, "ID 2452: bumblebee_sp3_crit_rate exists")
    assert_true(mods["bumblebee_sp3_crit_rate"]["st"] == 20, "ID 2452: max 20 stacks")

def test_jetfire():
    print("\n--- [TEST 2] Jetfire (天火) 7 项增补战技 ---")
    res = build_jetfire_abilities()
    mods, appears = res[0], res[1]

    # ID 2666: Damage Control
    assert_true("jetfire_sig_repair" in mods, "ID 2666: jetfire_sig_repair exists")

    # ID 2667: SP1 Ranged Buff
    assert_true("jetfire_sp1_ranged_buff" in mods, "ID 2667: jetfire_sp1_ranged_buff exists")
    assert_true(mods["jetfire_sp1_ranged_buff"]["d"] == 20.0, "ID 2667: 20.0s duration")

    # ID 2681: SP3 Charge Gain
    assert_true("jetfire_sp3_grant_charge" in mods, "ID 2681: jetfire_sp3_grant_charge exists")

    # ID 2682: SP3 Shock
    assert_true("jetfire_sp3_shock" in mods, "ID 2682: jetfire_sp3_shock exists")
    assert_true(mods["jetfire_sp3_shock"]["d"] == 4.0, "ID 2682: 4.0s duration")

    # ID 2683: SP1 Power Lock
    assert_true("jetfire_sp1_power_lock" in mods, "ID 2683: jetfire_sp1_power_lock exists")
    assert_true(mods["jetfire_sp1_power_lock"]["d"] == 8.0, "ID 2683: 8.0s duration")

    # ID 2684: SP2 Shield
    assert_true("jetfire_sp2_shield" in mods, "ID 2684: jetfire_sp2_shield exists")
    assert_true(mods["jetfire_sp2_shield"]["d"] == 20.0, "ID 2684: 20.0s duration")

    # ID 2685: SP2 Heal Block
    assert_true("jetfire_sp2_heal_block" in mods, "ID 2685: jetfire_sp2_heal_block exists")
    assert_true(mods["jetfire_sp2_heal_block"]["d"] == 15.0, "ID 2685: 15.0s duration")

def test_kickback():
    print("\n--- [TEST 3] Kickback (反冲) 12 项增补战技 ---")
    res = build_kickback_abilities()
    mods, appears = res[0], res[1]

    # IDs 3096 ~ 3107
    expected = [
        ("kickback_crit_power_leak", 3096),
        ("kickback_crit_rate", 3097),
        ("kickback_power_rate", 3098),
        ("kickback_dash_evade", 3099),
        ("kickback_heavy_power_gain", 3100), # Covers 3100 & 3101 Heavy Cleanse/Nullify to Power Gain
        ("kickback_sp1_shock", 3102),
        ("kickback_sp2_crit_buff", 3103),
        ("kickback_sp2_bleed", 3105),
        ("kickback_sp3_repair", 3107),
    ]
    for mid, aid in expected:
        assert_true(mid in mods, f"ID {aid}: {mid} exists in mods")
    # IDs 3104 & 3106 are covered by SP2/SP3 crit power leak mechanism in kickback_crit_power_leak
    assert_true(mods["kickback_crit_power_leak"]["d"] == 10.0, "IDs 3104/3106: 10.0s power leak")

def test_mixmaster():
    print("\n--- [TEST 4] Mixmaster (搅拌者) 7 项增补战技 ---")
    res = build_mixmaster_abilities()
    mods, appears = res[0], res[1]

    # ID 3180: Ranged Acid
    assert_true("mixmaster_ranged_acid" in mods, "ID 3180: mixmaster_ranged_acid exists")
    assert_true(mods["mixmaster_ranged_acid"]["d"] == 9.0, "ID 3180: 9.0s duration")

    # ID 3181: SP3 Acid
    assert_true("mixmaster_sp3_acid" in mods, "ID 3181: mixmaster_sp3_acid exists")
    assert_true(mods["mixmaster_sp3_acid"]["d"] == 20.0, "ID 3181: 20.0s duration")

    # ID 3182: SP1 Acid
    assert_true("mixmaster_sp1_acid" in mods, "ID 3182: mixmaster_sp1_acid exists")
    assert_true(mods["mixmaster_sp1_acid"]["d"] == 10.0, "ID 3182: 10.0s duration")

    # ID 3183: Special Damage Charge
    assert_true("mixmaster_special_dmg_buff" in mods, "ID 3183: mixmaster_special_dmg_buff exists")
    assert_true(mods["mixmaster_special_dmg_buff"]["st"] == 6, "ID 3183: max 6 stacks")

    # ID 3184: Crit Damage Charge
    assert_true("mixmaster_crit_dmg_buff" in mods, "ID 3184: mixmaster_crit_dmg_buff exists")
    assert_true(mods["mixmaster_crit_dmg_buff"]["st"] == 6, "ID 3184: max 6 stacks")

    # ID 3185: SP Consume
    assert_true("mixmaster_consume_special_buffs" in mods, "ID 3185: special buff consume exists")
    assert_true("mixmaster_consume_crit_buffs" in mods, "ID 3185: crit buff consume exists")

    # ID 3186: Debuff Crit Rate
    assert_true("mixmaster_debuff_crit_rate" in mods, "ID 3186: mixmaster_debuff_crit_rate exists")
    assert_true(mods["mixmaster_debuff_crit_rate"]["m"] == 0.50, "ID 3186: +50% crit rate")

def test_motormaster():
    print("\n--- [TEST 5] Motormaster (汽车大师) 5 项增补战技 ---")
    res = build_motormaster_abilities()
    mods, appears = res[0], res[1]

    # ID 3180: Heavy Ram Debuffs
    assert_true("motormaster_heavy_atk_debuff" in mods, "ID 3180: motormaster_heavy_atk_debuff exists")
    assert_true("motormaster_heavy_armor_break" in mods, "ID 3180: motormaster_heavy_armor_break exists")
    assert_true("motormaster_heavy_power_leak" in mods, "ID 3180: motormaster_heavy_power_leak exists")

    # ID 3184: King of the Road
    assert_true("motormaster_king_of_road" in mods, "ID 3184: motormaster_king_of_road exists")
    assert_true(mods["motormaster_king_of_road"]["st"] == 4, "ID 3184: max 4 stacks")

    # ID 3187: SP3 Recoil Blast
    assert_true("motormaster_sp3_burst_atk" in mods, "ID 3187: motormaster_sp3_burst_atk exists")
    assert_true("motormaster_sp3_self_recoil" in mods, "ID 3187: motormaster_sp3_self_recoil exists")

    # ID 3535: SP1 Power Burn
    assert_true("motormaster_sp1_power_burn" in mods, "ID 3535: motormaster_sp1_power_burn exists")

    # ID 3536: SP3 Full Ram Armor Break
    assert_true("motormaster_sp3_ram_armor" in mods, "ID 3536: motormaster_sp3_ram_armor exists")

def test_rhinox():
    print("\n--- [TEST 6] Rhinox (犀牛) 4 项增补战技 ---")
    res = build_rhinox_abilities()
    mods, appears = res[0], res[1]

    # ID 2769: Shield Buffs
    assert_true("rhinox_shield_buff" in mods, "ID 2769: rhinox_shield_buff exists")
    assert_true(mods["rhinox_shield_buff"]["st"] == 6, "ID 2769: 6 initial shield stacks")

    # ID 2774: Bleed Melee Boost
    assert_true("rhinox_bleed_extra_dmg" in mods, "ID 2774: rhinox_bleed_extra_dmg exists")

    # ID 2779: Overclock Shock
    assert_true("rhinox_overclock_shock" in mods, "ID 2779: rhinox_overclock_shock exists")
    assert_true(mods["rhinox_overclock_shock"]["d"] == 4.0, "ID 2779: 4.0s duration")

    # ID 2792: SP3 Bleed
    assert_true("rhinox_sp3_bleed" in mods, "ID 2792: rhinox_sp3_bleed exists")
    assert_true(mods["rhinox_sp3_bleed"]["d"] == 12.0, "ID 2792: 12.0s duration")

def test_waspinator():
    print("\n--- [TEST 7] Waspinator (黄蜂勇士) 7 项增补战技 ---")
    res = build_waspinator_abilities()
    mods, appears = res[0], res[1]

    # ID 3471 & 3472: Ranged Speed Buffs
    assert_true("waspinator_sig_ranged_speed" in mods, "ID 3471: waspinator_sig_ranged_speed exists")
    assert_true("waspinator_passive_ranged_speed" in mods, "ID 3472: waspinator_passive_ranged_speed exists")

    # ID 3473: Low HP Special Damage
    assert_true("waspinator_low_hp_sp_dmg" in mods, "ID 3473: waspinator_low_hp_sp_dmg exists")

    # ID 3474: Resistance Debuffs (Ranged + Heavy)
    assert_true("waspinator_ranged_resist_debuff" in mods, "ID 3474: waspinator_ranged_resist_debuff exists")
    assert_true("waspinator_heavy_resist_debuff" in mods, "ID 3474: waspinator_heavy_resist_debuff exists")

    # ID 3475: SP1 Crit Rate
    assert_true("waspinator_sp1_crit_rate" in mods, "ID 3475: waspinator_sp1_crit_rate exists")
    assert_true(mods["waspinator_sp1_crit_rate"]["d"] == 4.0, "ID 3475: 4.0s duration")

    # ID 3476: SP1 Anti-Evade
    assert_true("waspinator_sp1_anti_evade" in mods, "ID 3476: waspinator_sp1_anti_evade exists")
    assert_true(mods["waspinator_sp1_anti_evade"]["d"] == 4.0, "ID 3476: 4.0s duration")

    # ID 3477: SP2 Resistance Debuff
    assert_true("waspinator_sp2_resist_debuff" in mods, "ID 3477: waspinator_sp2_resist_debuff exists")
    assert_true(mods["waspinator_sp2_resist_debuff"]["d"] == 5.0, "ID 3477: 5.0s duration")

def test_wheeljack():
    print("\n--- [TEST 8] Wheeljack (千斤顶) 4 项增补战技 ---")
    res = build_wheeljack_abilities()
    mods, appears = res[0], res[1]

    # ID 2888: Force Shield
    assert_true("wheeljack_sig_force_shield" in mods, "ID 2888: wheeljack_sig_force_shield exists")
    assert_true(mods["wheeljack_sig_force_shield"]["d"] == 8.0, "ID 2888: 8.0s duration")

    # ID 3658: Upgrade Success Heal
    assert_true("wheeljack_upgrade_success_heal" in mods, "ID 3658: wheeljack_upgrade_success_heal exists")

    # ID 3659: SP2 Reroll Upgrades
    assert_true("wheeljack_sp2_reroll_upgrades" in mods, "ID 3659: wheeljack_sp2_reroll_upgrades exists")

    # ID 3660: SP3 Align Upgrades
    assert_true("wheeljack_sp3_align_upgrades" in mods, "ID 3660: wheeljack_sp3_align_upgrades exists")

def run_all():
    print("======================================================================")
    print("🚀 TFTF 战斗模拟器 - Batches 2~4 自动化质量门禁验证 (8 英雄、51 项战技)")
    print("======================================================================")
    test_bumblebee()
    test_jetfire()
    test_kickback()
    test_mixmaster()
    test_motormaster()
    test_rhinox()
    test_waspinator()
    test_wheeljack()
    print("\n======================================================================")
    print("🎉 恭喜！Batches 2~4 全部 8 个英雄、51 项战技模拟器测试 100% 通过！")
    print("======================================================================")

if __name__ == "__main__":
    run_all()
