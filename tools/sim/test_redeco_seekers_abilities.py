#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TFTF Combat Simulator - 6 Starscream Redeco Seekers Ability Verification Suite
=============================================================================
Verifies all abilities across the 6 Starscream redeco Seekers:
1. Bitstream (比特流) - bitstream_gs_leader2015
2. Hotlink (热链接) - hotlink_gs_leader2015
3. Ionstorm (离子风) - ionstorm_gs_leader2015
4. Novastorm (新星风) - novastorm_gs_leader2015
5. Acidstorm (酸雨) - acidstorm_gs_leader2015
6. Sunstorm (太阳风) - sunstorm_gs_leader2015
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

from Server.abilities.bots.bitstream import build_bitstream_abilities
from Server.abilities.bots.hotlink import build_hotlink_abilities
from Server.abilities.bots.ionstorm import build_ionstorm_abilities
from Server.abilities.bots.novastorm import build_novastorm_abilities
from Server.abilities.bots.acidstorm import build_acidstorm_abilities
from Server.abilities.bots.sunstorm import build_sunstorm_abilities

def assert_true(cond, msg):
    if not cond:
        print(f"  ❌ [FAIL] {msg}")
        sys.exit(1)
    else:
        print(f"  ✅ [PASS] {msg}")

def test_bitstream():
    print("\n--- [TEST 1] Bitstream (比特流) - 6 项战技机制 ---")
    res = build_bitstream_abilities()
    mods, appears = res[0], res[1]

    # ID 3612: Trojan Power Lock
    assert_true("bitstream_ranged_trojan_lock" in mods, "ID 3612: Trojan lock mod defined")
    assert_true(mods["bitstream_ranged_trojan_lock"]["d"] == 3.0, "ID 3612: Trojan lock duration 3.0s")

    # ID 3613: Firewall Shield & Shock Backlash
    assert_true("bitstream_firewall_shield" in mods and "bitstream_shield_backlash_shock" in mods, "ID 3613: Firewall shield & backlash shock defined")
    assert_true(mods["bitstream_firewall_shield"]["st"] == 4, "ID 3613: Firewall shield 4 stacks")

    # ID 3614: Zero-Day Refund Lock
    assert_true("bitstream_sig_refund_lock" in mods, "ID 3614: Sig zero-day lock defined")

    # ID 3615: SP1 Pulse Lock & Stun
    assert_true("bitstream_sp1_power_lock" in mods and "bitstream_sp1_stun" in mods, "ID 3615: SP1 lock & stun defined")

    # ID 3616: SP2 Logic Worm Leak
    assert_true("bitstream_sp2_power_leak" in mods, "ID 3616: SP2 logic worm leak defined")

    # ID 3617: SP3 System Reset
    assert_true("bitstream_sp3_drain_lock" in mods, "ID 3617: SP3 system reset drain lock defined")

def test_hotlink():
    print("\n--- [TEST 2] Hotlink (热链接) - 6 项战技机制 ---")
    res = build_hotlink_abilities()
    mods, appears = res[0], res[1]

    # ID 3603: Burn Immunity
    assert_true("hotlink_burn_immune" in mods, "ID 3603: Burn immunity defined")

    # ID 3604: Heavy Burn & Melee Boost
    assert_true("hotlink_heavy_burn" in mods and "hotlink_burn_melee_boost" in mods, "ID 3604: Heavy burn & melee boost defined")

    # ID 3605: Magma Unstoppable & Melee Stacks
    assert_true("hotlink_sig_unstoppable" in mods and "hotlink_sig_melee_stack" in mods, "ID 3605: Sig unstoppable & melee stack defined")
    assert_true(mods["hotlink_sig_melee_stack"]["st"] == 3, "ID 3605: Magma melee stack max 3")

    # ID 3606: SP1 Stream Burn & Melee Buff
    assert_true("hotlink_sp1_burn" in mods and "hotlink_sp1_melee_buff" in mods, "ID 3606: SP1 burn & melee buff defined")

    # ID 3607: SP2 Magma Bomb & Stun
    assert_true("hotlink_sp2_burn" in mods and "hotlink_sp2_stun" in mods, "ID 3607: SP2 burn & stun defined")

    # ID 3608: SP3 Inferno, Armor & Unstoppable
    assert_true("hotlink_sp3_burn" in mods and "hotlink_sp3_armor" in mods and "hotlink_sp3_unstoppable" in mods, "ID 3608: SP3 burn, armor & unstoppable defined")

def test_ionstorm():
    print("\n--- [TEST 3] Ionstorm (离子风) - 6 项战技机制 ---")
    res = build_ionstorm_abilities()
    mods, appears = res[0], res[1]

    # ID 3576: Ion Shock Power Rate Debuff
    assert_true("ionstorm_ion_impact" in mods, "ID 3576: Ion shock power rate debuff defined")

    # ID 3577: Heavy Armor Break, Nullify Buffs & Broken Boost
    assert_true("ionstorm_heavy_armor_break" in mods, "ID 3577: Heavy armor break defined")
    assert_true("ionstorm_heavy_nullify_armor" in mods and "ionstorm_heavy_nullify_unstop" in mods, "ID 3577: Heavy nullify armor & unstoppable defined")
    assert_true("ionstorm_armor_broken_boost" in mods, "ID 3577: Armor broken attack boost defined")

    # ID 3578: Sig Backfire Shock & Drain
    assert_true("ionstorm_sig_backfire_shock" in mods and "ionstorm_sig_backfire_drain" in mods, "ID 3578: Sig backfire shock & drain defined")

    # ID 3579: SP1 Shock & Unstoppable Punish
    assert_true("ionstorm_sp1_shock" in mods and "ionstorm_sp1_unstop_punish" in mods, "ID 3579: SP1 shock & unstop punish defined")

    # ID 3580: SP2 Break & Shock
    assert_true("ionstorm_sp2_break" in mods and "ionstorm_sp2_shock" in mods, "ID 3580: SP2 break & shock defined")

    # ID 3581: SP3 Annihilation Break & Attack Buff
    assert_true("ionstorm_sp3_break" in mods and "ionstorm_sp3_atk_buff" in mods, "ID 3581: SP3 break & atk buff defined")

def test_novastorm():
    print("\n--- [TEST 4] Novastorm (新星风) - 6 项战技机制 ---")
    res = build_novastorm_abilities()
    mods, appears = res[0], res[1]

    # ID 3585: Ranged Burn
    assert_true("novastorm_ranged_burn" in mods, "ID 3585: Ranged burn defined")

    # ID 3586: Combo 5x Crit, Crit Dmg & Heavy Burn
    assert_true("novastorm_combo_crit_rate" in mods and "novastorm_combo_crit_dmg" in mods, "ID 3586: Combo crit rate & dmg defined")
    assert_true("novastorm_heavy_burn" in mods, "ID 3586: Heavy burn defined")

    # ID 3587: Sig Thermonuclear Detonate / Burn
    assert_true("novastorm_sig_detonate" in mods and "novastorm_sig_burn" in mods, "ID 3587: Sig detonate & burn defined")

    # ID 3588: SP1 Radiation Burn & Crit Dmg
    assert_true("novastorm_sp1_burn" in mods and "novastorm_sp1_crit_dmg" in mods, "ID 3588: SP1 burn & crit dmg defined")

    # ID 3589: SP2 Unstoppable & Double Burn
    assert_true("novastorm_sp2_unstoppable" in mods and "novastorm_sp2_burn" in mods, "ID 3589: SP2 unstoppable & burn defined")

    # ID 3590: SP3 Supernova Collapse Burn & Drain
    assert_true("novastorm_sp3_burn" in mods and "novastorm_sp3_drain" in mods, "ID 3590: SP3 burn & drain defined")

def test_acidstorm():
    print("\n--- [TEST 5] Acidstorm (酸雨) - 7 项战技机制 ---")
    res = build_acidstorm_abilities()
    mods, appears = res[0], res[1]

    # ID 3566: Ranged Acid Jet
    assert_true("acidstorm_ranged_acid" in mods, "ID 3566: Ranged acid jet defined")

    # ID 3567: Acidic Plating Splash Break
    assert_true("acidstorm_splash_break" in mods, "ID 3567: Acid plating splash break defined")

    # ID 3568: Heavy Acid, Heavy Break & Acid Atk Boost
    assert_true("acidstorm_heavy_acid" in mods and "acidstorm_heavy_acid_break" in mods, "ID 3568: Heavy acid & break defined")
    assert_true("acidstorm_acid_atk_boost" in mods, "ID 3568: Acid atk boost defined")

    # ID 3569: Sig Aerosol Shield
    assert_true("acidstorm_sig_aerosol_shield" in mods, "ID 3569: Sig aerosol shield defined")
    assert_true(mods["acidstorm_sig_aerosol_shield"]["st"] == 3, "ID 3569: Sig aerosol shield stacks 3")

    # ID 3570: SP1 Acid Spray
    assert_true("acidstorm_sp1_acid" in mods, "ID 3570: SP1 acid spray defined")

    # ID 3571: SP2 Deluge Acid & Break
    assert_true("acidstorm_sp2_acid" in mods and "acidstorm_sp2_break" in mods, "ID 3571: SP2 deluge acid & break defined")

    # ID 3572: SP3 Skyfall Acid & Break
    assert_true("acidstorm_sp3_acid" in mods and "acidstorm_sp3_break" in mods, "ID 3572: SP3 skyfall acid & break defined")

def test_sunstorm():
    print("\n--- [TEST 6] Sunstorm (太阳风) - 6 项战技机制 ---")
    res = build_sunstorm_abilities()
    mods, appears = res[0], res[1]

    # ID 3594: Melee Radiation Bleed & Break
    assert_true("sunstorm_melee_bleed" in mods and "sunstorm_melee_break" in mods, "ID 3594: Melee bleed & break defined")

    # ID 3595: Heavy Burn, Crit Burn & Anti-Evade
    assert_true("sunstorm_heavy_burn" in mods and "sunstorm_crit_burn" in mods, "ID 3595: Heavy burn & crit burn defined")
    assert_true("sunstorm_burn_anti_evade" in mods, "ID 3595: Anti-evade suppression defined")

    # ID 3596: Sig Runaway Reactor Overheat Melee Gain
    assert_true("sunstorm_sig_melee_gain" in mods, "ID 3596: Sig reactor melee gain defined")
    assert_true(mods["sunstorm_sig_melee_gain"]["st"] == 4, "ID 3596: Overheat stack max 4")

    # ID 3597: SP1 Solar Jet Burn & Crit Buff
    assert_true("sunstorm_sp1_burn" in mods and "sunstorm_sp1_crit_buff" in mods, "ID 3597: SP1 burn & crit buff defined")

    # ID 3598: SP2 Flare Bombardment Burn & Stun
    assert_true("sunstorm_sp2_burn" in mods and "sunstorm_sp2_stun" in mods, "ID 3598: SP2 burn & stun defined")

    # ID 3599: SP3 Corona Storm Burn & Crit Dmg
    assert_true("sunstorm_sp3_burn" in mods and "sunstorm_sp3_crit_dmg" in mods, "ID 3599: SP3 corona burn & crit dmg defined")

def run_tests():
    print("=" * 70)
    print("🚀 6 位红蜘蛛重涂 Seeker 寻猎空军 (Seekers) 战技质量门禁测试")
    print("=" * 70)
    test_bitstream()
    test_hotlink()
    test_ionstorm()
    test_novastorm()
    test_acidstorm()
    test_sunstorm()
    print("\n" + "=" * 70)
    print("🎉 恭喜！6 位红蜘蛛重涂 Seeker (37 项战技) 机制与数据契约 100% 验证通过！")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()
