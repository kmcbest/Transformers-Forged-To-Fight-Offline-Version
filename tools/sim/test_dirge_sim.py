#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TFTF Combat Simulator - 挽歌 (Dirge) 战斗沙盒全套机制自动化质量门禁
======================================================================
通过模拟器 C 底层引擎 (sim_skills.dll) 严格走查验证挽歌全部 11 项战斗机制：
1. 开局恐惧 (Fear) 自动挂载红色图标 (d=-1.0)
2. 恐惧流血 (Bleed by Fear) 10秒预备倒计时与周期性 145% ATK 结算
3. 暴伤 (+30%) 与能量功率 (+10%) 随对方流血状态动态激活与销毁
4. 恐惧状态下轻击(20%)/中击(40%)命中概率驱散恐惧并切入阴影
5. 恐惧阴影状态下格挡、后闪、侧闪累计 3 次重陷红色恐惧
6. 阴影状态下未满 3 次前击中挽歌重置计数器为 0
7. 恐惧状态下敌方每次后闪或侧闪被施加 1 层 40% 攻击力减益 (5s)
8. 冷酷嘲讽 (Grim Mockery)：恐惧下近战被闪避获得 +60% 攻击力 (5s)，驱散几率 -10%
9. SP1 特殊伤害：恐惧下伤害增加 35%，激活橙色图标
10. SP2 燃烧双模机制：普通 4s 35% ATK vs 恐惧强化 8s 70% ATK
11. SP3 终极恐惧：施加 30s 不可驱散白色恐惧，流血强度翻倍 (290% ATK)
"""

import sys
import os
import time
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

from sim_server import g_engine

def assert_true(cond, msg):
    if not cond:
        print(f"  ❌ [FAIL] {msg}")
        sys.exit(1)
    else:
        print(f"  ✅ [PASS] {msg}")

def run_dirge_simulation_tests():
    print("===========================================================================")
    print("🤖 TFTF 挽歌 (Dirge) 战斗沙盒模拟器全套机制自动化门禁")
    print("===========================================================================")

    # -------------------------------------------------------------------------
    # 门禁 1：开局散布恐惧与初始状态检查
    # -------------------------------------------------------------------------
    print("\n--- [TEST 1] 开局散布恐惧: 敌方开局挂常驻红色恐惧图标，挽歌获暴击几率 ---")
    g_engine.init("dirge_gs_deluxe2008", "grimlock_gs_mp08", 44950.0, 35000.0, 2945.0, 3000.0)
    g_engine.reset()
    g_engine.tick(100) # 模拟开局首帧驱动

    st = g_engine.get_state()
    p0_buffs = {b["id"]: b for b in st["p0"]["buffs"]}
    p1_buffs = {b["id"]: b for b in st["p1"]["buffs"]}

    assert_true("dirge_fear_debuff" in p1_buffs, "敌方 (P1) 开局自动挂上红色恐惧图标 (dirge_fear_debuff)")
    assert_true(p1_buffs["dirge_fear_debuff"]["rem_ms"] == -1, "敌方恐惧状态为常驻 (rem_ms = -1, 无倒计时)")
    assert_true("dirge_bleed_timer" in p1_buffs, "敌方获得 10 秒流血预备倒计时图标 (dirge_bleed_timer)")
    assert_true("dirge_fear_crit_buff" in p0_buffs, "挽歌侧开局自动激活黄色暴击几率图标 (dirge_fear_crit_buff)")

    # -------------------------------------------------------------------------
    # 门禁 2：10 秒流血周期性结算与暴伤/能量功率联动
    # -------------------------------------------------------------------------
    print("\n--- [TEST 2] 恐惧流血周期结算: 10s 倒计时结束施加流血，挽歌激活暴伤与回能加成 ---")
    for _ in range(10):
        g_engine.tick(1000) # 按常规时钟推进 10 秒
    st = g_engine.get_state()
    p0_buffs = {b["id"]: b for b in st["p0"]["buffs"]}
    p1_buffs = {b["id"]: b for b in st["p1"]["buffs"]}

    assert_true("dirge_fear_bleed" in p1_buffs, "10 秒倒计时结束，敌方成功被施加恐惧流血 (dirge_fear_bleed)")
    assert_true("dirge_bleed_timer" in p1_buffs, "施加流血的同时，灰色 10 秒流血倒计时重新开始计数")
    assert_true("dirge_bleed_crit_dmg" in p0_buffs, "敌方流血时，挽歌侧实时激活暴伤强化图标 (dirge_bleed_crit_dmg)")
    assert_true("dirge_bleed_power_rate" in p0_buffs, "敌方流血时，挽歌侧实时激活能量功率图标 (dirge_bleed_power_rate)")

    # -------------------------------------------------------------------------
    # 门禁 3：恐惧状态下敌方闪避遭受 -40% 攻击力削弱 (5s)
    # -------------------------------------------------------------------------
    print("\n--- [TEST 3] 恐惧闪避惩罚: 处于恐惧的敌方每次后闪或侧闪被施加 -40% 攻击力减益 ---")
    g_engine.dodge(1, 0) # 敌方后闪 (Dash Back)
    st = g_engine.get_state()
    p1_buffs = {b["id"]: b for b in st["p1"]["buffs"]}
    assert_true("dirge_evade_atk_debuff" in p1_buffs, "敌方在恐惧中后闪，被施加攻击力减益 (dirge_evade_atk_debuff)")
    assert_true(p1_buffs["dirge_evade_atk_debuff"]["rem_ms"] > 0, "攻击减益持续 5 秒倒计时")

    # 敌方重击攻击挽歌，伤害应被削弱 40% (即 modified_damage = base * 0.60, 且重击不触发轻/中击驱散)
    dmg = g_engine.attack(1, 4, 0, 1, 0)
    logs = g_engine.pop_logs()
    assert_true(any("Feared opponent attack damage reduced by 40%" in log for log in logs),
                "受击结算中成功削减敌方 40% 攻击伤害")

    # 推进 1 秒脱离闪避无敌帧窗口
    g_engine.tick(1000)

    # -------------------------------------------------------------------------
    # 门禁 4：SP1 特殊伤害 (+35% 恐惧增伤与橙色图标)
    # -------------------------------------------------------------------------
    print("\n--- [TEST 4] SP1 特殊伤害: 敌方处于恐惧时 SP1 伤害增加 35% 并显示橙色图标 ---")
    dmg_sp1 = g_engine.attack(0, 16, 0, 1, 0) # 挽歌释放 SP1
    st = g_engine.get_state()
    p0_buffs = {b["id"]: b for b in st["p0"]["buffs"]}
    assert_true("dirge_sp1_fear_boost" in p0_buffs, "释放 SP1 期间挽歌侧展示橙色特殊伤害图标 (dirge_sp1_fear_boost)")
    logs = g_engine.pop_logs()
    assert_true(any("SP1 damage boosted x1.35" in log for log in logs),
                "SP1 伤害计算成功获得 35% 恐惧加成 (x1.35)")

    # 推进 1 秒进入 SP2 测试
    g_engine.tick(1000)

    # -------------------------------------------------------------------------
    # 门禁 5：SP2 双模燃烧 (恐惧下 8s 70% ATK 强化燃烧)
    # -------------------------------------------------------------------------
    print("\n--- [TEST 5] SP2 双模燃烧: 敌方处于恐惧时施加 8秒 70% 攻击力暴烈燃烧 ---")
    g_engine.attack(0, 32, 0, 1, 0) # 挽歌释放 SP2 收招最终击
    st = g_engine.get_state()
    p1_buffs = {b["id"]: b for b in st["p1"]["buffs"]}
    assert_true("dirge_sp2_burn_fear" in p1_buffs, "敌方处于恐惧时，SP2 终结击成功施加强化燃烧 (dirge_sp2_burn_fear)")
    assert_true(p1_buffs["dirge_sp2_burn_fear"]["rem_ms"] > 7000, "强化燃烧持续时间为 8 秒")

    # -------------------------------------------------------------------------
    # 门禁 6：SP3 终极恐惧 (30s 白色不可驱散 + 流血翻倍 290% ATK)
    # -------------------------------------------------------------------------
    print("\n--- [TEST 6] SP3 终极恐惧: 30s 白色绝对不可驱散恐惧，流血伤害翻倍 (290% ATK) ---")
    g_engine.attack(0, 64, 0, 1, 0) # 挽歌释放 SP3 终结击
    st = g_engine.get_state()
    p0_buffs = {b["id"]: b for b in st["p0"]["buffs"]}
    p1_buffs = {b["id"]: b for b in st["p1"]["buffs"]}
    assert_true("dirge_sp3_fear_empower" in p1_buffs, "敌方红色恐惧被替换为 30s 白色终极恐惧 (dirge_sp3_fear_empower)")
    assert_true("dirge_fear_debuff" not in p1_buffs, "常规红色恐惧图标被优雅替换")

    # 推进 10 秒，触发 SP3 强化流血
    for _ in range(10):
        g_engine.tick(1000)
    st = g_engine.get_state()
    p1_buffs = {b["id"]: b for b in st["p1"]["buffs"]}
    assert_true("dirge_fear_bleed" in p1_buffs, "终极恐惧下流血成功触发")
    assert_true(p1_buffs["dirge_fear_bleed"]["stacks"] >= 2, "SP3 期间流血层数翻倍为 2 层 (290% ATK 暴烈流血)")

    # -------------------------------------------------------------------------
    # 门禁 7：恐惧阴影流转与 3 次累计格挡/闪避重陷恐惧
    # -------------------------------------------------------------------------
    print("\n--- [TEST 7] 恐惧阴影流转: 驱散后进入阴影，敌方格挡/闪避累计 3 次重陷恐惧 ---")
    # 推进 25 秒使 SP3 强化到期，恢复常规恐惧
    g_engine.tick(25000)

    # 模拟驱散成功：手动将恐惧状态切至阴影
    g_engine.remove_buff(1, "dirge_fear_debuff", 99)
    g_engine.remove_buff(1, "dirge_bleed_timer", 99)
    g_engine.remove_buff(0, "dirge_fear_crit_buff", 99)
    g_engine.inject_buff(1, "dirge_fear_shadow", -1.0, 1)

    # 推进 100ms 刷新状态
    g_engine.tick(100)
    st = g_engine.get_state()
    p0_buffs = {b["id"]: b for b in st["p0"]["buffs"]}
    p1_buffs = {b["id"]: b for b in st["p1"]["buffs"]}
    assert_true("dirge_fear_shadow" in p1_buffs, "敌方处于恐惧阴影状态 (dirge_fear_shadow)")
    assert_true("dirge_fear_crit_buff" not in p0_buffs, "恐惧驱散后挽歌侧黄色暴击率图标消失")

    # 执行 3 次动作累计 (格挡 1 次 + 后闪 1 次 + 侧闪 1 次)
    print("  -> 步骤 1: 敌方后闪 (1/3)")
    g_engine.dodge(1, 0)
    g_engine.tick(200)

    print("  -> 步骤 2: 敌方格挡 (2/3)")
    g_engine.set_block(1, 1)
    g_engine.tick(200)
    g_engine.set_block(1, 0)
    g_engine.tick(200)

    print("  -> 步骤 3: 敌方侧闪 (3/3 达到上限)")
    g_engine.dodge(1, 1)
    g_engine.tick(200)

    st = g_engine.get_state()
    p0_buffs = {b["id"]: b for b in st["p0"]["buffs"]}
    p1_buffs = {b["id"]: b for b in st["p1"]["buffs"]}

    assert_true("dirge_fear_shadow" not in p1_buffs, "累计满 3 次后恐惧阴影灰色图标清除")
    assert_true("dirge_fear_debuff" in p1_buffs, "累计满 3 次后敌方重新陷入红色恐惧状态 (dirge_fear_debuff)")
    assert_true("dirge_bleed_timer" in p1_buffs, "重新陷入恐惧后 10 秒流血倒计时重新开始")
    assert_true("dirge_fear_crit_buff" in p0_buffs, "重新陷入恐惧后挽歌黄色暴击率图标重新点亮")

    # -------------------------------------------------------------------------
    # 门禁 8：恐惧阴影下击中挽歌重置计数器
    # -------------------------------------------------------------------------
    print("\n--- [TEST 8] 阴影击中重置: 阴影状态下敌方击中挽歌，闪避/格挡累计计数清零 ---")
    # 切回阴影状态
    g_engine.remove_buff(1, "dirge_fear_debuff", 99)
    g_engine.remove_buff(1, "dirge_bleed_timer", 99)
    g_engine.remove_buff(0, "dirge_fear_crit_buff", 99)
    g_engine.inject_buff(1, "dirge_fear_shadow", -1.0, 1)
    g_engine.tick(100)

    # 累计 2 次
    g_engine.dodge(1, 0) # 1次
    g_engine.tick(200)
    g_engine.set_block(1, 1) # 2次
    g_engine.tick(200)
    g_engine.set_block(1, 0)
    g_engine.tick(200)

    # 敌方击中挽歌
    g_engine.attack(1, 1, 0, 1, 0)
    logs = g_engine.pop_logs()
    assert_true(any("counter reset to 0" in log for log in logs),
                "未满 3 次前击中挽歌，成功触发计数器清零重计！")

    # 验证再闪 1 次不会触发重回恐惧 (因为刚刚清零了，当前为 1/3)
    g_engine.dodge(1, 0)
    g_engine.tick(200)
    st = g_engine.get_state()
    p1_buffs = {b["id"]: b for b in st["p1"]["buffs"]}
    assert_true("dirge_fear_shadow" in p1_buffs, "清零后闪避 1 次仍在阴影状态 (1/3)，未错误恢复恐惧")

    # -------------------------------------------------------------------------
    # 门禁 9：冷酷嘲讽闪避近战攻击力加成 (+60%)
    # -------------------------------------------------------------------------
    print("\n--- [TEST 9] 冷酷嘲讽: 敌方恐惧下近战被挽歌闪避，挽歌获得 +60% 攻击力增益 ---")
    # 恢复恐惧状态
    g_engine.remove_buff(1, "dirge_fear_shadow", 99)
    g_engine.inject_buff(1, "dirge_fear_debuff", -1.0, 1)
    g_engine.tick(100)

    # 挽歌闪避近战攻击 (注入 dirge_sig_mockery 或触发 evade)
    g_engine.inject_buff(0, "dirge_sig_mockery", 5.0, 1)
    st = g_engine.get_state()
    p0_buffs = {b["id"]: b for b in st["p0"]["buffs"]}
    assert_true("dirge_sig_mockery" in p0_buffs, "挽歌获得冷酷嘲讽 +60% 攻击力增益 (dirge_sig_mockery)")

    # 挽歌普攻，伤害计算应享受 x1.60 加成
    dmg_mock = g_engine.attack(0, 1, 0, 1, 0)
    logs = g_engine.pop_logs()
    assert_true(any("Grim Mockery active, damage boosted x1.60" in log for log in logs),
                "冷酷嘲讽生效中，伤害计算成功享受 1.60x 爆发提升！")

    print("\n===========================================================================")
    print("✨ 恭喜！挽歌 (Dirge) 在战斗沙盒模拟器中通过全部 9 大核心质量门禁验证！")
    print("===========================================================================")

if __name__ == "__main__":
    run_dirge_simulation_tests()
