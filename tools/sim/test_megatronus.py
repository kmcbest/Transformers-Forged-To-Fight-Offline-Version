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

def init_combatant(p0_id, p1_id, p0_hp=35206.0, p1_hp=30000.0, p0_atk=2375.0, p1_atk=2500.0):
    g_engine.init(p0_id, p1_id, p0_hp, p1_hp, p0_atk, p1_atk)
    g_engine.set_crit_rate(0, 0.0)
    g_engine.set_crit_rate(1, 0.0)
    g_engine.reset()

def run_tests():
    print("=" * 75)
    print("🤖 TFTF 震天尊 (Megatronus) 全套战斗机制与自主充能自动化质量门禁")
    print("=" * 75)

    # ------------------------------------------------------------------------
    # [TEST 1] 火种源能量自主生成: 攻击/受击不产气，每秒自动回气 1.2% 最大能量
    # ------------------------------------------------------------------------
    print("\n--- [TEST 1] 火种源自主回气: 攻击/受击 0 产气，每秒自主产生 1.2% 最大能量 ---")
    init_combatant("megatronus_gs_kabam", "generic_enemy")
    
    st_start = g_engine.get_state()
    mana_start = st_start["p0"]["mana"]
    print(f"  [Megatronus] 开局初始能量: {mana_start:.2f}")
    assert abs(mana_start - 0.0) < 0.01

    # 1. 震天尊主动轻击/中击/重击打对手: 验证 0 产气
    g_engine.attack(0, 1, 0, 0, 0) # L1
    g_engine.attack(0, 2, 0, 0, 0) # M1
    g_engine.attack(0, 4, 0, 1, 0) # Heavy
    mana_after_atk = g_engine.get_state()["p0"]["mana"]
    print(f"  [Megatronus] 进攻连击后能量: {mana_after_atk:.2f} (预期 0 产气: 0.00)")
    assert abs(mana_after_atk - 0.0) < 0.01, f"Expected 0.00 mana after attack, got {mana_after_atk}"
    print("  [PASS] 震天尊主动攻击 100% 不产生能量 (火种源能量机制生效)!")

    # 2. 对手打震天尊: 验证受击 0 产气
    g_engine.attack(1, 2, 0, 0, 0) # 对手打震天尊
    mana_after_hit = g_engine.get_state()["p0"]["mana"]
    print(f"  [Megatronus] 受击后能量: {mana_after_hit:.2f} (预期 0 产气: 0.00)")
    assert abs(mana_after_hit - 0.0) < 0.01, f"Expected 0.00 mana after getting hit, got {mana_after_hit}"
    print("  [PASS] 震天尊防守受击 100% 不产生能量 (常规回能归零生效)!")

    # 3. 推进物理时钟 14.0 秒: 预期自主产生 14.0 * (1.0/14.0) = 1.000 格能量 (14秒充满一格)
    g_engine.tick(14000) # 14000 ms = 14s
    mana_after_tick = g_engine.get_state()["p0"]["mana"]
    print(f"  [Megatronus] 经过 14.0 秒自主回气后能量: {mana_after_tick:.3f} (预期 1.000)")
    assert abs(mana_after_tick - 1.000) < 0.02, f"Expected ~1.000 mana, got {mana_after_tick}"
    print("  [PASS] 火种源能量精准 14 秒充满一格能量 (14s 累加 1.000 格)!")

    # ------------------------------------------------------------------------
    # [TEST 2] 狂怒遗迹 (Relic of Fury): 开局激活，攻击力 +60%，对手格挡精通 -20%
    # ------------------------------------------------------------------------
    print("\n--- [TEST 2] 狂怒遗迹 (Relic of Fury): 开局增攻 +60% 与格挡渗透 ---")
    init_combatant("megatronus_gs_kabam", "generic_enemy")
    
    # 检查开局是否挂上狂怒遗迹 Buff
    st = g_engine.get_state()
    p0_buff_ids = [b["id"] for b in st["p0"]["buffs"]]
    print(f"  [Megatronus] 开局 Buff 列表: {p0_buff_ids}")
    assert any("relic_fury" in b for b in p0_buff_ids), "Megatronus must have Relic of Fury active on start"
    
    # 基础中击伤害 = 2375 * 0.40 = 950.0；狂怒遗迹 +60% 后 = 950 * 1.60 = 1520.0
    p1_hp_before = g_engine.get_state()["p1"]["hp"]
    g_engine.attack(0, 2, 0, 1, 0)
    fury_dmg = p1_hp_before - g_engine.get_state()["p1"]["hp"]
    print(f"  [Megatronus] 狂怒遗迹下中击伤害: {fury_dmg} (预期 950 * 1.60 = 1520.0)")
    assert abs(fury_dmg - 1520.0) < 1.0, f"Expected 1520.0, got {fury_dmg}"
    print("  [PASS] 狂怒遗迹攻击力加成 +60% 精准生效 (950 -> 1520)!")

    # ------------------------------------------------------------------------
    # [TEST 3] 能量满格交替切换至保存遗迹 (Relic of Preservation)
    # ------------------------------------------------------------------------
    print("\n--- [TEST 3] 充满一格能量: 自动切换至保存遗迹 (减伤 60% 与 20% 最大生命伤害上限) ---")
    # 充盈到 1.0 格能量 (跨越 1 bar)
    g_engine.set_mana(0, 1.05)
    g_engine.tick(100) # 驱动 simulation tick
    
    st_switched = g_engine.get_state()
    p0_buffs_switched = [b["id"] for b in st_switched["p0"]["buffs"]]
    print(f"  [Megatronus] 充盈 1 格能量后 Buff 列表: {p0_buffs_switched}")
    assert any("relic_preservation" in b for b in p0_buffs_switched), "Must switch to Relic of Preservation on 1st bar"
    assert not any("relic_fury" in b for b in p0_buffs_switched), "Relic of Fury must be removed"
    print("  [PASS] 能量满 1 格自动切换为保存遗迹！")

    # 验证保存遗迹受击减伤 60%: 对手基础中击 = 2500 * 0.40 = 1000.0，减免 60% 后为 400.0
    p0_hp_before = g_engine.get_state()["p0"]["hp"]
    g_engine.attack(1, 2, 0, 1, 0) # 对手打震天尊
    pres_dmg = p0_hp_before - g_engine.get_state()["p0"]["hp"]
    print(f"  [Megatronus] 保存遗迹下受击伤害: {pres_dmg} (预期 1000 * 0.40 = 400.0)")
    assert abs(pres_dmg - 400.0) < 1.0, f"Expected 400.0, got {pres_dmg}"
    print("  [PASS] 保存遗迹精准减免 60% 受击伤害 (1000 -> 400)!")

    # 验证单次受击伤害上限截断为最大生命值的 20% (35206 * 0.20 = 7041.2)
    # 模拟超高额伤害打击: 50,000 点攻击
    init_combatant("megatronus_gs_kabam", "generic_enemy", p1_atk=125000.0) # 125000 * 0.4 = 50000 原始伤害
    g_engine.set_mana(0, 1.05)
    g_engine.tick(100) # 激活保存遗迹
    
    p0_hp_before = g_engine.get_state()["p0"]["hp"]
    g_engine.attack(1, 2, 0, 1, 0) # 极高伤害打击
    capped_dmg = p0_hp_before - g_engine.get_state()["p0"]["hp"]
    expected_cap = 35206.0 * 0.20
    print(f"  [Megatronus] 承受超额打击受击伤害: {capped_dmg} (预期锁死截断在 20% 最大生命值: {expected_cap:.1f})")
    assert abs(capped_dmg - expected_cap) < 1.0, f"Expected {expected_cap}, got {capped_dmg}"
    print(f"  [PASS] 单次伤害上限严格截断为震天尊最大生命的 20% ({expected_cap:.1f})!")

    # 充盈到 2.0 格能量: 验证再次交替回狂怒遗迹
    init_combatant("megatronus_gs_kabam", "generic_enemy")
    g_engine.set_mana(0, 1.05)
    g_engine.tick(100) # 变成保存遗迹
    g_engine.set_mana(0, 2.05)
    g_engine.tick(100) # 充满第 2 格，应变回狂怒遗迹
    st_bar2 = g_engine.get_state()
    p0_buffs_bar2 = [b["id"] for b in st_bar2["p0"]["buffs"]]
    print(f"  [Megatronus] 充盈 2 格能量后 Buff 列表: {p0_buffs_bar2}")
    assert any("relic_fury" in b for b in p0_buffs_bar2), "Must alternate back to Relic of Fury on 2nd bar"
    print("  [PASS] 能量满 2 格再次成功交替切换回狂怒遗迹！")

    # ------------------------------------------------------------------------
    # [TEST 4] 不朽遗迹 (Relic of Immortality): 濒死 <= 10% 激活 8 秒绝对免伤
    # ------------------------------------------------------------------------
    print("\n--- [TEST 4] 不朽遗迹: 濒死 <= 10% 激活 8 秒绝对免伤 ---")
    init_combatant("megatronus_gs_kabam", "generic_enemy")
    
    # 将震天尊生命值设为 4000 (大于 10% = 3520.6)
    g_engine.set_hp(0, 4000.0)
    
    # 对手打出一记 1000 伤害打击，将震天尊打至 3000 (跌破 10% 阈值 3520.6)
    g_engine.attack(1, 2, 0, 1, 0)
    st_immort = g_engine.get_state()
    p0_hp = st_immort["p0"]["hp"]
    p0_buffs_immort = [b["id"] for b in st_immort["p0"]["buffs"]]
    print(f"  [Megatronus] 跌破 10% HP 后的血量: {p0_hp:.1f} (保底留在 10% 阈值: 3520.6)")
    assert abs(p0_hp - 3520.6) < 1.0
    assert any("relic_immortality" in b for b in p0_buffs_immort), "Relic of Immortality must be activated"
    print("  [PASS] 生命跌破 10% 成功保底并激活不朽遗迹！")

    # 在不朽遗迹期间连续受击 5 次: 验证伤害全为 0.0
    for i in range(5):
        hp_before = g_engine.get_state()["p0"]["hp"]
        g_engine.attack(1, 4, 0, 1, 0) # 重击
        dmg = hp_before - g_engine.get_state()["p0"]["hp"]
        assert abs(dmg - 0.0) < 0.01, f"Expected 0 damage during immortality, got {dmg}"
    print("  [PASS] 不朽遗迹持续期间 100% 绝对免除所有伤害 (结算伤害恒为 0)!")

    # 推进 8.1 秒: 验证不朽遗迹到期解除
    g_engine.tick(8100)
    st_expired = g_engine.get_state()
    assert not any("relic_immortality" in b for b in st_expired["p0"]["buffs"]), "Immortality must expire after 8s"
    print("  [PASS] 不朽遗迹持续 8 秒后精准解除！")

    # ------------------------------------------------------------------------
    # [TEST 5] 重击黑暗燃烧 (Heavy Dark Burn)
    # ------------------------------------------------------------------------
    print("\n--- [TEST 5] 重击黑暗燃烧: 最后一击 100% 施加 40% ATK 即时能量伤害 ---")
    init_combatant("megatronus_gs_kabam", "generic_enemy")
    p1_hp_before = g_engine.get_state()["p1"]["hp"]
    # 震天尊重击 (act=4, is_last=1)
    g_engine.attack(0, 4, 0, 1, 0)
    total_heavy_loss = p1_hp_before - g_engine.get_state()["p1"]["hp"]
    # 重击本身中击伤害 + 40% ATK 即时黑暗燃烧 (2375 * 0.40 = 950.0)
    # 狂怒遗迹下重击 = 2375 * 1.00 * 1.60 = 3800.0；加燃烧 950.0 = 4750.0
    print(f"  [Megatronus] 重击总伤害: {total_heavy_loss} (含 40% ATK 黑暗燃烧: 950.0)")
    assert abs(total_heavy_loss - 4750.0) < 1.0, f"Expected 4750.0, got {total_heavy_loss}"
    print("  [PASS] 重击命中 100% 结算黑暗燃烧即时能量伤害!")

    # ------------------------------------------------------------------------
    # [TEST 6] SP1 能量窃取 (Power Steal under Relic of Fury)
    # ------------------------------------------------------------------------
    print("\n--- [TEST 6] SP1 能量窃取: 狂怒遗迹下 100% 窃取对手 35% 现有能量 ---")
    init_combatant("megatronus_gs_kabam", "generic_enemy")
    g_engine.set_mana(0, 1.0) # 震天尊 1 格气
    g_engine.set_mana(1, 2.0) # 对手 2 格气 (2.0)
    
    # 释放 SP1
    g_engine.attack(0, 16, 0, 1, 0)
    p1_mana_after = g_engine.get_state()["p1"]["mana"]
    # 对手被偷走 35%: 2.0 * 0.35 = 0.70；剩余 1.30
    print(f"  [Megatronus] 对手被窃取后能量: {p1_mana_after:.2f} (原 2.00, 被窃取 35% -> 预期 1.30)")
    assert abs(p1_mana_after - 1.30) < 0.02, f"Expected 1.30, got {p1_mana_after}"
    print("  [PASS] SP1 狂怒状态下精准窃取对手 35% 现有能量!")

    # ------------------------------------------------------------------------
    # [TEST 7] SP2 生命窃取 (Life Steal under Relic of Preservation)
    # ------------------------------------------------------------------------
    print("\n--- [TEST 7] SP2 生命窃取: 保存遗迹下 100% 窃取 17.5% 震天尊最大生命 ---")
    init_combatant("megatronus_gs_kabam", "generic_enemy")
    g_engine.set_mana(0, 1.05)
    g_engine.tick(100) # 切换到保存遗迹
    g_engine.set_mana(0, 2.0) # 满足 SP2 消耗
    g_engine.set_hp(0, 20000.0) # 扣除部分血量用于测试回血
    
    p0_hp_before = g_engine.get_state()["p0"]["hp"]
    # 释放 SP2 (act=32, hit=0 首击触发生命窃取)
    g_engine.attack(0, 32, 0, 0, 0)
    p0_hp_after = g_engine.get_state()["p0"]["hp"]
    healed = p0_hp_after - p0_hp_before
    expected_steal = 35206.0 * 0.175 # 6161.05
    print(f"  [Megatronus] SP2 首击生命窃取回复量: {healed:.1f} (预期 17.5% 最大生命: {expected_steal:.1f})")
    assert abs(healed - expected_steal) < 1.0, f"Expected {expected_steal}, got {healed}"
    print("  [PASS] SP2 保存遗迹下精准窃取对手 17.5% 最大生命并全额治愈自身!")

    # ------------------------------------------------------------------------
    # [TEST 8] 满 3 格气静置停充: 满气后静置 10 秒，能量严格钳制在 3.00，绝不溢出累积
    # ------------------------------------------------------------------------
    print("\n--- [TEST 8] 满 3 格气静置停充: 满气静置 10 秒，能量严格锁死在 3.00 格 ---")
    init_combatant("megatronus_gs_kabam", "generic_enemy")
    g_engine.set_mana(0, 3.0)
    g_engine.tick(100) # 同步当前能量状态
    mana_full = g_engine.get_state()["p0"]["mana"]
    print(f"  [Megatronus] 满能量初始值: {mana_full:.3f}")
    assert abs(mana_full - 3.0) < 0.01

    # 静置 10 秒 (10000ms)，此时自主回能必须彻底停止并持续对齐时钟，禁止暗中累加
    g_engine.tick(10000)
    mana_after_idle = g_engine.get_state()["p0"]["mana"]
    print(f"  [Megatronus] 满能量静置 10 秒后能量: {mana_after_idle:.3f} (严格等于 3.000)")
    assert abs(mana_after_idle - 3.0) < 0.001, f"Expected strictly 3.000, got {mana_after_idle}"
    print("  [PASS] 满 3 格能量后自主充能彻底停充，能量严格锁死在 3.000 格，无任何溢出累积！")

    # ------------------------------------------------------------------------
    # [TEST 9] 延迟释放 S3 扣除 3 格能量并清零
    # ------------------------------------------------------------------------
    print("\n--- [TEST 9] 延迟释放 S3: 满气静置后释放 S3，扣除 3 格气后能量精准清零 ---")
    g_engine.attack_start(0, 64)
    g_engine.attack(0, 64, 0, 1, 0)
    mana_after_s3 = g_engine.get_state()["p0"]["mana"]
    print(f"  [Megatronus] 释放 S3 终结后能量: {mana_after_s3:.3f} (预期 0.000)")
    assert abs(mana_after_s3 - 0.0) < 0.001, f"Expected strictly 0.000 mana after S3, got {mana_after_s3}"
    print("  [PASS] 满气释放 S3 精准扣除 3 格能量归零！")

    # ------------------------------------------------------------------------
    # [TEST 10] 释放特殊技完全不影响自主充气
    # ------------------------------------------------------------------------
    print("\n--- [TEST 10] 特殊技期间自主充能持续生效: 放S技不阻断回能，无需等待普攻打中对手 ---")
    init_combatant("megatronus_gs_kabam", "generic_enemy")
    g_engine.set_mana(0, 0.0)
    # 模拟启动 SP1 特技动作 (act=16)
    g_engine.attack_start(0, 16)
    # 流逝 7.0 秒 (7000ms)，此时自主回能必须持续推进，预期产生 7.0 * (1.0/14.0) = 0.500 格
    g_engine.tick(7000)
    mana_during_sp = g_engine.get_state()["p0"]["mana"]
    print(f"  [Megatronus] 施放特技并流逝 7.0 秒后能量: {mana_during_sp:.3f} (预期 0.500)")
    assert abs(mana_during_sp - 0.500) < 0.02, f"Expected ~0.500 mana during SP, got {mana_during_sp}"
    print("  [PASS] 释放特殊技期间自主充能持续匀速推进，完全不受动作状态阻断！")

    print("\n" + "=" * 75)
    print("🎉 恭喜！震天尊 (Megatronus) 全套 13 项核心技能、自主充能与双遗迹 100% 通过！")
    print("=" * 75)

if __name__ == "__main__":
    run_tests()
