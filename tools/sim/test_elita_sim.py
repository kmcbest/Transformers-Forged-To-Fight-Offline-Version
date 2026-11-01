#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TFTF Combat Simulator - Elita-1 (艾丽塔) Ability Verification Suite
==================================================================
Verifies all 14 priority combat abilities of Elita-1 (elita_one_gs / elita_one_gs_kabam):
- SP1: Armor Break, Brawler Bonus, Power Burn
- SP2: Nullify, Shock DOT
- SP3: Bleed DOT, Tactical Lockdown
- Passives: Tactical Insight Evade & Buff, Nimble Counter Stun & Weaken, Joint Aim Pierce & Refresh,
            Ranged Crit Armor Break, Commander's Presence DOT Acceleration
- Signature: Resistance Flame ATK/Crit at 50%, Armor at 25%, SP Interrupt Stun
- Synergies: Eternal Bond Shield, Resistance Sisters Crit & Heavy
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

from Server.abilities.bots.elita_one import build_elita_abilities

def assert_true(cond, msg):
    if not cond:
        print(f"  ❌ [FAIL] {msg}")
        sys.exit(1)
    else:
        print(f"  ✅ [PASS] {msg}")

def test_elita_priority_abilities():
    print("\n--- [TEST] Elita-1 (艾丽塔) 14 项优先战技机制与数据契约 ---")
    mods, appears, buffs = build_elita_abilities(38400.0, 2780.0)

    # 1. SP1
    assert_true("elita_sp1_armor_break" in mods, "SP1: Armor break defined")
    assert_true(mods["elita_sp1_armor_break"]["m"] == 0.35, "SP1: 35% armor reduction")
    assert_true("elita_sp1_armor_break_braw" in mods, "SP1: Brawler extra armor break defined")
    assert_true(mods["elita_sp1_armor_break_braw"]["m"] == 0.15, "SP1: Extra 15% armor reduction vs Brawlers (total 50%)")
    assert_true("elita_sp1_power_burn" in mods, "SP1: Power burn defined")

    # 2. SP2
    assert_true("elita_sp2_nullify" in mods, "SP2: Nullify defined")
    assert_true(mods["elita_sp2_nullify"]["c"] == 0.80, "SP2: 80% nullify chance")
    assert_true("elita_sp2_shock" in mods, "SP2: Shock defined")
    assert_true(mods["elita_sp2_shock"]["m"] == 2780.0, "SP2: Shock total damage 100% ATK (2780)")
    assert_true(mods["elita_sp2_shock"]["d"] == 10.0, "SP2: Shock duration 10s")

    # 3. SP3
    assert_true("elita_sp3_bleed" in mods, "SP3: Bleed defined")
    assert_true(mods["elita_sp3_bleed"]["m"] == 3336.0, "SP3: Bleed total damage 120% ATK (3336)")
    assert_true(mods["elita_sp3_bleed"]["d"] == 6.0, "SP3: Bleed duration 6s")
    assert_true("elita_sp3_tactical_lockdown" in mods, "SP3: Tactical lockdown defined")
    assert_true(mods["elita_sp3_tactical_lockdown"]["d"] == 8.0, "SP3: Tactical lockdown duration 8s")

    # 4. Passives
    assert_true("elita_tactical_insight_evade" in mods, "Passive: Tactical insight evade defined")
    assert_true("elita_tactical_insight_melee_buff" in mods, "Passive: Tactical insight melee buff defined")
    assert_true(mods["elita_tactical_insight_melee_buff"]["m"] == 0.30, "Passive: Tactical insight melee buff 30%")

    assert_true("elita_counter_pouch_buff" in mods, "Passive: Nimble counter pouch defined")
    assert_true(mods["elita_counter_pouch_buff"]["d"] == 1.0, "Passive: Counter pouch duration 1.0s")
    assert_true(mods["elita_counter_pouch_buff"]["p"] == 0.50, "Passive: Counter pouch chance 50%")
    assert_true("elita_counter_stun" in mods, "Passive: Counter stun defined")
    assert_true(mods["elita_counter_stun"]["d"] == 1.5, "Passive: Counter stun duration 1.5s")
    assert_true("elita_counter_atk_debuff" in mods, "Passive: Counter attack debuff defined")
    assert_true(mods["elita_counter_atk_debuff"]["m"] == -0.50, "Passive: Counter attack debuff -50%")

    assert_true("elita_joint_aim_pierce" in mods, "Passive: Joint aim armor pierce defined")
    assert_true(mods["elita_joint_aim_pierce"]["m"] == 1.0, "Passive: Joint aim 100% armor pierce")
    assert_true("elita_joint_aim_refresh" in mods, "Passive: Joint aim refresh debuffs defined")
    assert_true(mods["elita_joint_aim_refresh"]["p"] == 0.70, "Passive: Joint aim 70% refresh chance")

    assert_true("elita_ranged_crit_armor_break" in mods, "Passive: Ranged crit armor break defined")
    assert_true(mods["elita_ranged_crit_armor_break"]["m"] == 0.50, "Passive: Ranged crit armor break 50%")

    assert_true("elita_commanders_presence" in mods, "Passive: Commander's presence defined")
    assert_true(mods["elita_commanders_presence"]["m"] == 0.20, "Passive: Commander's presence accelerates DOT 20%")

    # 5. Signature
    assert_true("elita_sig_flame_atk_50" in mods, "Sig: Flame ATK boost at 50% HP defined")
    assert_true(mods["elita_sig_flame_atk_50"]["m"] == 0.50, "Sig: Flame ATK boost 50%")
    assert_true("elita_sig_flame_crit_50" in mods, "Sig: Flame Crit boost at 50% HP defined")
    assert_true(mods["elita_sig_flame_crit_50"]["m"] == 0.50, "Sig: Flame Crit boost 50%")
    assert_true("elita_sig_flame_armor_25" in mods, "Sig: Flame Armor boost at 25% HP defined")
    assert_true(mods["elita_sig_flame_armor_25"]["m"] == 0.90, "Sig: Flame Armor boost 90%")
    assert_true("elita_sig_flame_interrupt_stun" in mods, "Sig: Flame SP interrupt stun defined")
    assert_true("elita_sig_flame_interrupt_stun_braw" in mods, "Sig: Flame SP interrupt stun vs Brawler defined")

    # 6. Synergies
    assert_true("elita_synergy_eternal_bond_shield" in mods, "Synergy: Eternal bond shield defined")
    assert_true(mods["elita_synergy_eternal_bond_shield"]["m"] == 5760.0, "Synergy: 15% Max HP Shield (38400 * 0.15 = 5760)")
    assert_true("elita_synergy_sisters_crit" in mods, "Synergy: Sisters crit boost defined")
    assert_true("elita_synergy_sisters_heavy" in mods, "Synergy: Sisters heavy boost defined")

    print("\n🎉 艾丽塔全部优先战技在模拟器检验中 100% 验证通过！")

if __name__ == "__main__":
    test_elita_priority_abilities()
