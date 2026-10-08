#!/usr/bin/env python3
"""
Unit Tests for Evade Combat Abilities (Bumblebee & Barricade)
=============================================================
测试目标:
1. 验证小黄蜂 (bumblebee_gs_kabam) 与路障 (barricade_cin_dotm) 成功被能力总引擎加载并注册；
2. 验证小黄蜂后闪触发 32% 消耗型近战规避 (无倒计时, 触发规避后消耗)；
3. 验证路障被击倒触发 85% 3秒近战规避、85% 3秒远程规避、40% 7.5秒暴击几率增益；
4. 验证矢量图标 (PUA 0xe509, 0xe518, 0xe406) 与颜色契约 (纯6位十六进制, 严禁带 '#')；
5. 验证 build_buffs_config 和 build_buffs_set 包含 evade_melee, evade_ranged, crit_rate。
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from abilities import (
    bot_abilities,
    build_stat_mods,
    build_stat_mod_appears,
    build_buffs_config,
    build_buffs_set,
)
from abilities.registry import get_registered_bots, get_bot_mod_ids

BEE_ID = "bumblebee_gs_kabam"
BARRICADE_ID = "barricade_cin_dotm"


class TestEvadeAbilities(unittest.TestCase):
    def test_bots_registered(self):
        """验证小黄蜂与路障已在能力引擎中正确注册。"""
        registered = get_registered_bots()
        self.assertIn(BEE_ID, registered, f"{BEE_ID} 必须已注册")
        self.assertIn(BARRICADE_ID, registered, f"{BARRICADE_ID} 必须已注册")

    def test_bumblebee_evade_contract(self):
        """验证小黄蜂后闪近战规避能力修饰器与外观表现契约。"""
        stat_mods = build_stat_mods()
        appears = build_stat_mod_appears()

        mod_id = "bumblebee_dodge_evade_melee"
        self.assertIn(mod_id, stat_mods)
        mod = stat_mods[mod_id]

        self.assertEqual(mod["t"], "evade_melee")
        self.assertEqual(mod["tr"], ["onPlayerStateEnter"])
        self.assertEqual(mod["trs"], "state=Dodge")
        self.assertEqual(mod["c"], 1.0)       # 后闪 100% 获得近战规避图标
        self.assertEqual(mod["d"], -1.0)  # 无倒计时
        self.assertTrue(mod.get("consume_on_evade"))
        self.assertEqual(mod["ta"], "self")
        self.assertEqual(mod["mt"], "buff")

        appr_id = "appr_bumblebee_dodge_evade_melee"
        self.assertIn(appr_id, appears)
        appr = appears[appr_id]
        self.assertEqual(appr["t"], "\uE509")  # 近战规避 PUA 0xe509
        self.assertEqual(appr["tc"], "10B981") # 绿色 (无 '#')
        self.assertNotIn("#", appr["tc"])
        self.assertEqual(appr["st"], "")       # 后闪挂图标时不弹字，规避触发时弹“规避”大字

    def test_barricade_abilities_contract(self):
        """验证路障被击倒起身后触发的近战规避、远程规避与暴击几率契约。"""
        stat_mods = build_stat_mods()
        appears = build_stat_mod_appears()

        # 1. 近战规避 (3.0秒倒计时型，起身后持续3s)
        m_melee = stat_mods.get("barricade_knockdown_evade_melee")
        self.assertIsNotNone(m_melee)
        self.assertEqual(m_melee["t"], "evade_melee")
        self.assertEqual(m_melee["tr"], ["onAnimStateEnter"])
        self.assertEqual(m_melee["trs"], "currAnim=StandupFromBack,StandupFromFront")
        self.assertEqual(m_melee["c"], 0.85)   # 85% 获得几率
        self.assertEqual(m_melee["m"], 0.85)   # 85% 规避几率
        self.assertEqual(m_melee["d"], 3.0)
        self.assertFalse(m_melee.get("consume_on_evade"))

        a_melee = appears.get("appr_barricade_knockdown_evade_melee")
        self.assertIsNotNone(a_melee)
        self.assertEqual(a_melee["t"], "\uE509")
        self.assertEqual(a_melee["tc"], "10B981")
        self.assertEqual(a_melee["st"], "")    # 起身获得时不弹字，触发规避时呼出“规避”

        # 2. 远程规避 (3.0秒倒计时型，起身后持续3s)
        m_ranged = stat_mods.get("barricade_knockdown_evade_ranged")
        self.assertIsNotNone(m_ranged)
        self.assertEqual(m_ranged["t"], "evade_ranged")
        self.assertEqual(m_ranged["tr"], ["onAnimStateEnter"])
        self.assertEqual(m_ranged["trs"], "currAnim=StandupFromBack,StandupFromFront")
        self.assertEqual(m_ranged["c"], 0.85)
        self.assertEqual(m_ranged["m"], 0.85)
        self.assertEqual(m_ranged["d"], 3.0)

        a_ranged = appears.get("appr_barricade_knockdown_evade_ranged")
        self.assertIsNotNone(a_ranged)
        self.assertEqual(a_ranged["t"], "\uE518")
        self.assertEqual(a_ranged["tc"], "10B981")
        self.assertEqual(a_ranged["st"], "")    # 起身获得时不弹字，触发规避时呼出“规避”

        # 3. 暴击几率 (7.5秒倒计时型，起身后持续7.5s)
        m_crit = stat_mods.get("barricade_knockdown_crit_rate")
        self.assertIsNotNone(m_crit)
        self.assertEqual(m_crit["t"], "crit_rate")
        self.assertEqual(m_crit["tr"], ["onAnimStateEnter"])
        self.assertEqual(m_crit["trs"], "currAnim=StandupFromBack,StandupFromFront")
        self.assertEqual(m_crit["c"], 0.40)
        self.assertEqual(m_crit["d"], 7.5)

        a_crit = appears.get("appr_barricade_knockdown_crit_rate")
        self.assertIsNotNone(a_crit)
        self.assertEqual(a_crit["t"], "\uE406")
        self.assertEqual(a_crit["tc"], "F59E0B")
        self.assertEqual(a_crit["st"], "暴击几率")

        # 4. 验证 bot_abilities 列表包含全部 3 个修饰器
        b_mods = bot_abilities(BARRICADE_ID)
        self.assertIn("barricade_knockdown_evade_melee", b_mods)
        self.assertIn("barricade_knockdown_evade_ranged", b_mods)
        self.assertIn("barricade_knockdown_crit_rate", b_mods)

    def test_buffs_config_and_set(self):
        """验证全局 Buff 配置库中注册了规避与暴击增益。"""
        cfg = build_buffs_config()
        groups = cfg["groups"]
        self.assertIn("evade_melee", groups)
        self.assertTrue(groups["evade_melee"]["active_display"])
        self.assertIn("evade_ranged", groups)
        self.assertTrue(groups["evade_ranged"]["active_display"])
        self.assertIn("crit_rate", groups)
        self.assertTrue(groups["crit_rate"]["active_display"])

        b_set = build_buffs_set()
        global_buffs = b_set["globalBuffs"]
        self.assertIn("evade_melee", global_buffs)
        self.assertIn("evade_ranged", global_buffs)
        self.assertIn("crit_rate", global_buffs)


if __name__ == "__main__":
    unittest.main()
