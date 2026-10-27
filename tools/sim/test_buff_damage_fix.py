# -*- coding: utf-8 -*-
import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.sim.sim_server import g_engine

def init_combatant(p0_id, p1_id):
    g_engine.init(p0_id, p1_id, 30000.0, 30000.0, 2500.0, 2500.0)
    g_engine.set_crit_rate(0, 0.0)
    g_engine.set_crit_rate(1, 0.0)
    g_engine.reset()

def run_tests():
    print("=" * 70)
    print("🛡️ TFTF 全角色护甲减伤与近战/攻击力增益验证套件")
    print("=" * 70)
    
    # ------------------------------------------------------------------------
    # [TEST 1] 电影擎天柱 (Movie Optimus Prime): 护甲减伤与近战增伤
    # ------------------------------------------------------------------------
    print("\n--- [TEST 1] 电影擎天柱 (Movie Optimus Prime): 护甲减伤与近战增伤 ---")
    init_combatant("optimusprime_cin_tf", "generic_enemy")
    
    # 1. 基础近战与远程攻击 (无 Buff): 中击 40% ATK = 1000
    p1_hp_before = g_engine.get_state()["p1"]["hp"]
    g_engine.attack(0, 2, 0, 1, 0) # P0 中击 P1
    base_melee_dmg = p1_hp_before - g_engine.get_state()["p1"]["hp"]
    print(f"  [Optimus] 无 Buff 基础中击伤害: {base_melee_dmg}")
    assert abs(base_melee_dmg - 1000.0) < 1.0, f"Expected 1000.0, got {base_melee_dmg}"
    
    # 2. 注入近战增益 (optimusprime_cin_tf_melee_buff): 近战伤害 +60% (1000 -> 1600)
    g_engine.inject_buff(0, "optimusprime_cin_tf_melee_buff", 4.0, 1)
    p1_hp_before = g_engine.get_state()["p1"]["hp"]
    g_engine.attack(0, 2, 0, 1, 0) # P0 中击 P1
    boosted_melee_dmg = p1_hp_before - g_engine.get_state()["p1"]["hp"]
    print(f"  [Optimus] 注入近战增益后中击伤害: {boosted_melee_dmg} (预期 +60% = 1600.0)")
    assert abs(boosted_melee_dmg - 1600.0) < 1.0, f"Expected 1600.0, got {boosted_melee_dmg}"
    print("  [PASS] 电影擎天柱近战增益精准提升 +60% 伤害 (1000.0 -> 1600.0)!")

    # 3. 严格排除远程射击 (远程射击不得享受近战增益)
    # 远程基础伤害 = 2500 * 0.35 = 875.0
    p1_hp_before = g_engine.get_state()["p1"]["hp"]
    g_engine.attack(0, 8, 0, 1, 0) # P0 远程射击
    ranged_dmg = p1_hp_before - g_engine.get_state()["p1"]["hp"]
    print(f"  [Optimus] 近战增益下远程射击伤害: {ranged_dmg} (预期保持 875.0 不受加成)")
    assert abs(ranged_dmg - 875.0) < 1.0, f"Expected 875.0, got {ranged_dmg}"
    print("  [PASS] 电影擎天柱近战增益严格限定近战，远程射击未受误加成!")

    # 4. 护甲减伤结算: 敌人中击伤害本应为 1000.0
    p0_hp_before = g_engine.get_state()["p0"]["hp"]
    g_engine.attack(1, 2, 0, 1, 0) # 敌方打擎天柱
    dmg_taken_raw = p0_hp_before - g_engine.get_state()["p0"]["hp"]
    print(f"  [Optimus] 无护甲受击伤害: {dmg_taken_raw}")
    assert abs(dmg_taken_raw - 1000.0) < 1.0

    # 注入护甲增益 (optimusprime_cin_tf_block_armor): 减伤 16.5% (1000 -> 835.0)
    g_engine.inject_buff(0, "optimusprime_cin_tf_block_armor", 7.0, 1)
    p0_hp_before = g_engine.get_state()["p0"]["hp"]
    g_engine.attack(1, 2, 0, 1, 0) # 敌方打擎天柱
    dmg_taken_armor = p0_hp_before - g_engine.get_state()["p0"]["hp"]
    print(f"  [Optimus] 获得护甲后受击伤害: {dmg_taken_armor} (预期降低 16.5% = 835.0)")
    assert abs(dmg_taken_armor - 835.0) < 1.0, f"Expected 835.0, got {dmg_taken_armor}"
    print("  [PASS] 电影擎天柱护甲增益精准生效减伤 16.5% (1000.0 -> 835.0)!")

    # ------------------------------------------------------------------------
    # [TEST 2] 钢锁 (Grimlock): 受击近战(+25%)、SP1(+40%)、SP2(+60%)
    # ------------------------------------------------------------------------
    print("\n--- [TEST 2] 钢锁 (Grimlock): 多重近战增益加成 ---")
    init_combatant("grimlock_gs_mp08", "generic_enemy")
    
    # 无 Buff 基础伤害: 1000.0
    p1_hp_before = g_engine.get_state()["p1"]["hp"]
    g_engine.attack(0, 2, 0, 1, 0)
    base_g_dmg = p1_hp_before - g_engine.get_state()["p1"]["hp"]
    assert abs(base_g_dmg - 1000.0) < 1.0
    
    # 注入受击近战增益 (grimlock_takehit_melee_buff): +25% (1000 -> 1250.0)
    g_engine.inject_buff(0, "grimlock_takehit_melee_buff", 4.0, 1)
    p1_hp_before = g_engine.get_state()["p1"]["hp"]
    g_engine.attack(0, 2, 0, 1, 0)
    hit_buff_dmg = p1_hp_before - g_engine.get_state()["p1"]["hp"]
    print(f"  [Grimlock] 受击近战增益伤害: {hit_buff_dmg} (预期 +25% = 1250.0)")
    assert abs(hit_buff_dmg - 1250.0) < 1.0, f"Expected 1250.0, got {hit_buff_dmg}"
    print("  [PASS] 钢锁受击近战增益 +25% 生效!")

    # 注入 SP1 近战增益 (grimlock_sp1_melee_buff): +40% (1000 -> 1400.0)
    g_engine.remove_buff(0, "grimlock_takehit_melee_buff", 1)
    g_engine.inject_buff(0, "grimlock_sp1_melee_buff", 6.0, 1)
    p1_hp_before = g_engine.get_state()["p1"]["hp"]
    g_engine.attack(0, 2, 0, 1, 0)
    sp1_buff_dmg = p1_hp_before - g_engine.get_state()["p1"]["hp"]
    print(f"  [Grimlock] SP1近战增益伤害: {sp1_buff_dmg} (预期 +40% = 1400.0)")
    assert abs(sp1_buff_dmg - 1400.0) < 1.0, f"Expected 1400.0, got {sp1_buff_dmg}"
    print("  [PASS] 钢锁 SP1 近战增益 +40% 生效!")

    # 注入 SP2 近战增益 (grimlock_sp2_melee_buff): +60% (1000 -> 1600.0)
    g_engine.remove_buff(0, "grimlock_sp1_melee_buff", 1)
    g_engine.inject_buff(0, "grimlock_sp2_melee_buff", 6.0, 1)
    p1_hp_before = g_engine.get_state()["p1"]["hp"]
    g_engine.attack(0, 2, 0, 1, 0)
    sp2_buff_dmg = p1_hp_before - g_engine.get_state()["p1"]["hp"]
    print(f"  [Grimlock] SP2近战增益伤害: {sp2_buff_dmg} (预期 +60% = 1600.0)")
    assert abs(sp2_buff_dmg - 1600.0) < 1.0, f"Expected 1600.0, got {sp2_buff_dmg}"
    print("  [PASS] 钢锁 SP2 近战增益 +60% 生效!")

    # ------------------------------------------------------------------------
    # [TEST 3] 野牛 (Tantrum): 格挡护甲(-16.5%) 与 SP3 近战(+80%)
    # ------------------------------------------------------------------------
    print("\n--- [TEST 3] 野牛 (Tantrum): 格挡护甲与 SP3 近战增益 ---")
    init_combatant("tantrum_gs_kabam", "generic_enemy")
    
    # 1. 护甲减伤: 1000 -> 835.0
    g_engine.inject_buff(0, "tantrum_block_armor", 3.0, 1)
    p0_hp_before = g_engine.get_state()["p0"]["hp"]
    g_engine.attack(1, 2, 0, 1, 0)
    tan_armor_dmg = p0_hp_before - g_engine.get_state()["p0"]["hp"]
    print(f"  [Tantrum] 护甲减伤受击伤害: {tan_armor_dmg} (预期降低 16.5% = 835.0)")
    assert abs(tan_armor_dmg - 835.0) < 1.0, f"Expected 835.0, got {tan_armor_dmg}"
    print("  [PASS] 野牛格挡护甲减伤 16.5% 生效!")

    # 2. SP3 近战增益: +80% (1000 -> 1800.0)
    g_engine.inject_buff(0, "tantrum_sp3_melee_buff", 8.0, 1)
    p1_hp_before = g_engine.get_state()["p1"]["hp"]
    g_engine.attack(0, 2, 0, 1, 0)
    tan_sp3_dmg = p1_hp_before - g_engine.get_state()["p1"]["hp"]
    print(f"  [Tantrum] SP3近战增益伤害: {tan_sp3_dmg} (预期 +80% = 1800.0)")
    assert abs(tan_sp3_dmg - 1800.0) < 1.0, f"Expected 1800.0, got {tan_sp3_dmg}"
    print("  [PASS] 野牛 SP3 强力近战增益 +80% 生效!")

    # ------------------------------------------------------------------------
    # [TEST 4] 惊天雷 (Thundercracker): SP1 近战增益 (+50%)
    # ------------------------------------------------------------------------
    print("\n--- [TEST 4] 惊天雷 (Thundercracker): SP1 近战增益 ---")
    init_combatant("thundercracker_gs_leader2015", "generic_enemy")
    g_engine.inject_buff(0, "thundercracker_sp1_melee_buff", 6.0, 1)
    p1_hp_before = g_engine.get_state()["p1"]["hp"]
    g_engine.attack(0, 2, 0, 1, 0)
    tc_sp1_dmg = p1_hp_before - g_engine.get_state()["p1"]["hp"]
    print(f"  [Thundercracker] SP1近战增益伤害: {tc_sp1_dmg} (预期 +50% = 1500.0)")
    assert abs(tc_sp1_dmg - 1500.0) < 1.0, f"Expected 1500.0, got {tc_sp1_dmg}"
    print("  [PASS] 惊天雷 SP1 近战增益 +50% 生效!")

    # ------------------------------------------------------------------------
    # [TEST 5] 巨蝎勇士 (Scorponok): 毒液充能增伤 (+20%/层)
    # ------------------------------------------------------------------------
    print("\n--- [TEST 5] 巨蝎勇士 (Scorponok): 毒液充能增伤 ---")
    init_combatant("scorponok_bw_kabam", "generic_enemy")
    # 3 层毒液充能: +60% (1000 -> 1600.0)
    g_engine.inject_buff(0, "scorponok_venom_charge", -1.0, 3)
    p1_hp_before = g_engine.get_state()["p1"]["hp"]
    g_engine.attack(0, 2, 0, 1, 0)
    scorp_dmg = p1_hp_before - g_engine.get_state()["p1"]["hp"]
    print(f"  [Scorponok] 3层毒液充能伤害: {scorp_dmg} (预期 +60% = 1600.0)")
    assert abs(scorp_dmg - 1600.0) < 1.0, f"Expected 1600.0, got {scorp_dmg}"
    print("  [PASS] 巨蝎勇士毒液充能增伤 (+20%/层) 生效!")

    # ------------------------------------------------------------------------
    # [TEST 6] 通用托底 (Universal Fallback - 如 G1 擎天柱、铁皮等未挂独立C模块角色)
    # ------------------------------------------------------------------------
    print("\n--- [TEST 6] 通用托底机制 (G1 擎天柱 optimus 等未挂独立 C 模块角色) ---")
    init_combatant("fte_optimus_gs_t3", "generic_enemy")
    
    # 1. 通用护甲减伤托底 (optimus_block_armor / armor_up)
    g_engine.inject_buff(0, "optimus_block_armor", 2.5, 1)
    p0_hp_before = g_engine.get_state()["p0"]["hp"]
    g_engine.attack(1, 2, 0, 1, 0)
    g1_armor_dmg = p0_hp_before - g_engine.get_state()["p0"]["hp"]
    print(f"  [G1 Optimus] 护甲增益通用受击伤害: {g1_armor_dmg} (预期降低 16.5% = 835.0)")
    assert abs(g1_armor_dmg - 835.0) < 1.0, f"Expected 835.0, got {g1_armor_dmg}"
    print("  [PASS] G1 擎天柱通用护甲减伤 16.5% 托底生效!")

    # 2. 通用攻击力增益托底 (attack_buff / attack_boost: +20%)
    g_engine.inject_buff(0, "optimus_sp1_atk_buff", 6.0, 1) # matches attack_buff
    p1_hp_before = g_engine.get_state()["p1"]["hp"]
    g_engine.attack(0, 2, 0, 1, 0)
    g1_atk_dmg = p1_hp_before - g_engine.get_state()["p1"]["hp"]
    print(f"  [G1 Optimus] 攻击增益通用伤害: {g1_atk_dmg} (预期 +20% = 1200.0)")
    assert abs(g1_atk_dmg - 1200.0) < 1.0, f"Expected 1200.0, got {g1_atk_dmg}"
    print("  [PASS] G1 擎天柱通用攻击力增益 +20% 托底生效!")

    print("\n" + "=" * 70)
    print("🎉 恭喜！电影擎天柱、钢锁、野牛、惊天雷、巨蝎及通用角色护甲/加攻全线 100% 验证通过！")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()
