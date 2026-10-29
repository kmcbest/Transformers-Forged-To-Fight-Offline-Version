#!/usr/bin/env python3
"""
TFTF Combat Simulator - Batch 1 Ability Verification Suite
==========================================================
Verifies Hot Rod, G1 Optimus, Cyclonus, Slipstream, G1 Megatron, and Cheetor
mechanisms in the combat simulator environment.
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

from sim_server import g_engine, CURRENT_MATCHUP
from Server.abilities.bots.hotrod import build_hotrod_abilities
from Server.abilities.bots.optimus import build_optimus_abilities
from Server.abilities.bots.cyclonus import build_cyclonus_abilities
from Server.abilities.bots.slipstream import build_slipstream_abilities
from Server.abilities.bots.megatron import build_megatron_abilities
from Server.abilities.bots.cheetor import build_cheetor_abilities

def assert_true(cond, msg):
    if not cond:
        print(f"  ❌ [FAIL] {msg}")
        sys.exit(1)
    else:
        print(f"  ✅ [PASS] {msg}")

def test_hotrod_adjusted_stun():
    print("\n--- [TEST 1] Hot Rod (ID 2550): Heavy Stun Duration Adjusted to 1.5s ---")
    mods, appears = build_hotrod_abilities()
    assert_true("hotrod_heavy_stun" in mods, "hotrod_heavy_stun exists in mods")
    stun_mod = mods["hotrod_heavy_stun"]
    assert_true(stun_mod["d"] == 1.5, f"Stun duration is exactly 1.5s (got {stun_mod['d']}s)")
    assert_true(stun_mod["c"] == 0.40, f"Stun chance is 40% (got {stun_mod['c']})")
    assert_true("level=Heavy" in stun_mod["trs"], "Trigger scope restricted to Heavy attack")
    assert_true(stun_mod["ta"] == "opponent", "Stun targets opponent")

def test_optimus_heavy_attack_buff():
    print("\n--- [TEST 2] G1 Optimus (ID 2357): Heavy Attack Buff (+115.2% ATK, 7.0s) ---")
    mods, appears = build_optimus_abilities()
    assert_true("optimus_heavy_atk_buff" in mods, "optimus_heavy_atk_buff exists in mods")
    atk_mod = mods["optimus_heavy_atk_buff"]
    assert_true(atk_mod["d"] == 7.0, f"Attack buff duration is 7.0s (got {atk_mod['d']}s)")
    assert_true(abs(atk_mod["m"] - 1.152) < 1e-4, f"Attack boost is +115.2% (got {atk_mod['m']*100:.1f}%)")
    assert_true("onPlayerStateEnter" in atk_mod["tr"], "Triggered on player state enter")
    assert_true(atk_mod["trs"] == "state=Heavy", "Trigger scope restricted to Heavy state")

def test_cyclonus_dark_energy():
    print("\n--- [TEST 3] Cyclonus (ID 2972): Dark Energy on Power Bar Fill (+30% ATK, 6.0s) ---")
    mods, appears, buffs = build_cyclonus_abilities()
    assert_true("cyclonus_dark_energy_power_fill" in mods, "cyclonus_dark_energy_power_fill exists in mods")
    de_mod = mods["cyclonus_dark_energy_power_fill"]
    assert_true(de_mod["d"] == 6.0, f"Dark Energy duration is 6.0s (got {de_mod['d']}s)")
    assert_true(de_mod["m"] == 0.30, f"Dark Energy attack bonus is +30% (got {de_mod['m']*100:.0f}%)")
    assert_true("onPowerBarFull" in de_mod["tr"], "Triggered on power bar full")
    assert_true(de_mod["st"] == 3, f"Dark energy max stacks is 3 (got {de_mod['st']})")

def test_slipstream_ranged_nullify():
    print("\n--- [TEST 4] Slipstream (ID 3354): Ranged Nullify Shield ---")
    mods, appears, buffs = build_slipstream_abilities()
    assert_true("slipstream_ranged_nullify_shield" in mods, "slipstream_ranged_nullify_shield exists in mods")
    null_mod = mods["slipstream_ranged_nullify_shield"]
    assert_true("level=Ranged" in null_mod["trs"], "Trigger restricted to Ranged")
    assert_true(null_mod["c"] == 1.0, "100% chance to nullify shield")
    assert_true(null_mod["ta"] == "opponent", "Targets opponent")

def test_megatron_unstoppable_and_no_mercy():
    print("\n--- [TEST 5] G1 Megatron (ID 3126 & 3127): Unstoppable & No Mercy ---")
    mods, appears = build_megatron_abilities()
    # ID 3126
    assert_true("megatron_knockdown_unstoppable" in mods, "megatron_knockdown_unstoppable exists in mods")
    unst_mod = mods["megatron_knockdown_unstoppable"]
    assert_true(unst_mod["d"] == 3.0, f"Unstoppable duration is 3.0s (got {unst_mod['d']}s)")
    assert_true("onKnockdown" in unst_mod["tr"], "Triggered on knockdown")
    # ID 3127
    assert_true("megatron_no_mercy_steal" in mods, "megatron_no_mercy_steal exists in mods")
    steal_mod = mods["megatron_no_mercy_steal"]
    assert_true(steal_mod["d"] == 5.0, f"Buff steal duration is 5.0s (got {steal_mod['d']}s)")
    assert_true(steal_mod["c"] == 0.60, f"Buff steal chance is 60% (got {steal_mod['c']})")

def test_cheetor_all_priority_abilities():
    print("\n--- [TEST 6] Cheetor (IDs 2472~2480): Full Suite Verification in Simulator ---")
    base_hp = 28245.0
    base_atk = 2874.0
    mods, appears, buffs = build_cheetor_abilities(base_hp=base_hp, base_atk=base_atk)

    # 1. ID 2472: Power Guard
    assert_true("cheetor_power_guard" in mods, "ID 2472: cheetor_power_guard exists")
    assert_true(mods["cheetor_power_guard"]["t"] == "passive", "Power Guard is passive")

    # 2. ID 2473: Crit Bleed
    assert_true("cheetor_crit_bleed" in mods, "ID 2473: cheetor_crit_bleed exists")
    assert_true(mods["cheetor_crit_bleed"]["d"] == 4.0, "Crit bleed lasts 4.0s")
    assert_true(abs(mods["cheetor_crit_bleed"]["m"] - round(base_atk * 0.65, 2)) < 1.0, "Bleed dmg is 65% ATK")

    # 3. ID 2474: Combo Power Gain
    assert_true("cheetor_combo_power_gain" in mods, "ID 2474: cheetor_combo_power_gain exists")
    assert_true("level=Light4,Medium2" in mods["cheetor_combo_power_gain"]["trs"], "Trigger scope is Light4,Medium2")

    # 4. ID 2475: Heavy Evade Range
    assert_true("cheetor_heavy_evade_ranged" in mods, "ID 2475: cheetor_heavy_evade_ranged exists")
    assert_true("level=Heavy" in mods["cheetor_heavy_evade_ranged"]["trs"], "Heavy evade trigger scope is Heavy")

    # 5. ID 2476: SP1 Bleed
    assert_true("cheetor_sp1_bleed" in mods, "ID 2476: cheetor_sp1_bleed exists")
    assert_true(mods["cheetor_sp1_bleed"]["d"] == 8.0, "SP1 bleed lasts 8.0s")
    assert_true(abs(mods["cheetor_sp1_bleed"]["m"] - round(base_atk * 1.00, 2)) < 1.0, "SP1 bleed dmg is 100% ATK")

    # 6. ID 2477: SP2 Power Rate
    assert_true("cheetor_sp2_power_buff" in mods, "ID 2477: cheetor_sp2_power_buff exists")
    assert_true(mods["cheetor_sp2_power_buff"]["d"] == 12.0, "SP2 power buff lasts 12.0s")
    assert_true(mods["cheetor_sp2_power_buff"]["m"] == 0.50, "SP2 power rate bonus is +50%")

    # 7. ID 2478: SP3 Damage Increase
    assert_true("cheetor_sp3_dmg_amp" in mods, "ID 2478: cheetor_sp3_dmg_amp exists")
    assert_true("onSpecial3Activate" in mods["cheetor_sp3_dmg_amp"]["tr"], "SP3 amp triggers onSpecial3Activate")

    # 8. ID 2479: SP3 Power Lock
    assert_true("cheetor_sp3_power_lock" in mods, "ID 2479: cheetor_sp3_power_lock exists")
    assert_true(mods["cheetor_sp3_power_lock"]["d"] == 10.0, "SP3 power lock lasts 10.0s")

    # 9. ID 2480: SP3 Power Burn
    assert_true("cheetor_sp3_power_burn" in mods, "ID 2480: cheetor_sp3_power_burn exists")
    assert_true(mods["cheetor_sp3_power_burn"]["m"] == -9.0, "SP3 burns 3% max energy (9 mana points)")

    # Simulator Matchup Execution
    print("\n--- [SIMULATOR RUN] Simulating Cheetor vs Barricade in Engine ---")
    g_engine.init("cheetor_bw_transmetal", "barricade_cin_dotm", 28245.0, 28245.0, 2874.0, 2874.0)
    st = g_engine.get_state()
    assert_true(st["p0"]["hp"] == 28245.0, "Cheetor initialized with 28245 HP")
    assert_true(st["p1"]["hp"] == 28245.0, "Barricade initialized with 28245 HP")

    # Simulate basic hit & tick
    g_engine.attack(0, 0, 0, True, False)
    g_engine.tick(500)
    st = g_engine.get_state()
    assert_true(st["p1"]["hp"] < 28245.0, "Opponent took damage from Cheetor attack")

if __name__ == "__main__":
    print("=======================================================================")
    print("🚀 TFTF 战斗模拟器 - 头一批技能 (Batch 1) 行为与契约自动化测试")
    print("=======================================================================")
    test_hotrod_adjusted_stun()
    test_optimus_heavy_attack_buff()
    test_cyclonus_dark_energy()
    test_slipstream_ranged_nullify()
    test_megatron_unstoppable_and_no_mercy()
    test_cheetor_all_priority_abilities()
    print("\n=======================================================================")
    print("🎉 恭喜！头一批技能 (6 角色 15 项能力) 在战斗模拟器中 100% 全部通过！")
    print("=======================================================================")
