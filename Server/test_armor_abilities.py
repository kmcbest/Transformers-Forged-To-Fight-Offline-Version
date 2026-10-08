#!/usr/bin/env python3
"""
Unit Tests for Armor & Armor Break Abilities (G1 Optimus, Ultra Magnus, Grindor)
================================================================================
测试目标:
1. 验证 G1 擎天柱 (fte_optimus_gs_t3)、通天晓 (ultramagnus_gs_leader) 与碾碎器 (grindor_cin_rotf) 正确注册；
2. 验证 G1 擎天柱的 6 项能力 (格挡护甲、SP1 破甲、SP1 攻击加成、SP2 破甲、SP3 破甲、觉醒技突破口流血联动)；
3. 验证通天晓的 6 项能力 (SP1/SP2/SP3 破甲、重击/SP2/SP3 燃烧)；
4. 验证碾碎器的 2 项能力 (受击护甲、重击暴击燃烧)；
5. 验证底层契约安全性 (颜色纯6位十六进制、PUA字形正确、列表包装合规)；
6. 验证全局 build_buffs_config 和 build_buffs_set 包含 armor_up, armor_break, attack_buff, dmg_burn。
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
from abilities.registry import get_registered_bots

OPTIMUS_ID = "fte_optimus_gs_t3"
MAGNUS_ID = "ultramagnus_gs_leader"
GRINDOR_ID = "grindor_cin_rotf"


class TestArmorAbilities(unittest.TestCase):
    def test_bots_registered(self):
        """验证 G1 擎天柱、通天晓与碾碎器成功注册。"""
        registered = get_registered_bots()
        self.assertIn(OPTIMUS_ID, registered)
        self.assertIn(MAGNUS_ID, registered)
        self.assertIn(GRINDOR_ID, registered)

    def test_g1_optimus_contract(self):
        """验证 G1 擎天柱全套能力与突破口机制契约。"""
        stat_mods = build_stat_mods()
        appears = build_stat_mod_appears()

        # 1. 格挡护甲 (ID 2355)
        m_armor = stat_mods.get("optimus_block_armor")
        self.assertIsNotNone(m_armor)
        self.assertEqual(m_armor["t"], "armor_up")
        self.assertEqual(m_armor["tr"], ["onPlayerStateEnter"])
        self.assertEqual(m_armor["trs"], "state=Block")
        self.assertEqual(m_armor["m"], 0.165)
        self.assertEqual(m_armor["d"], 2.5)
        self.assertEqual(m_armor["ta"], "self")
        self.assertEqual(m_armor["mt"], "buff")

        a_armor = appears.get("appr_optimus_block_armor")
        self.assertIsNotNone(a_armor)
        self.assertEqual(a_armor["t"], "\uE517")  # 完整胸甲 PUA
        self.assertEqual(a_armor["tc"], "29EBF4") # 官方电光青色 (真机取色)
        self.assertEqual(a_armor["gb"], "00C5E8")
        self.assertNotIn("#", a_armor["tc"])

        # 2. SP1 破甲 (ID 2354) - 仅后两击巨斧劈砍 (index=1,2)
        m_sp1_break = stat_mods.get("optimus_sp1_armor_break")
        self.assertIsNotNone(m_sp1_break)
        self.assertEqual(m_sp1_break["t"], "armor_break")
        self.assertEqual(m_sp1_break["trs"], "level=Special1;index=1,2")
        self.assertEqual(m_sp1_break["m"], 0.20)
        self.assertEqual(m_sp1_break["d"], 3.5)
        self.assertEqual(m_sp1_break["ta"], "opponent")
        self.assertEqual(m_sp1_break["mt"], "debuff")

        a_sp1_break = appears.get("appr_optimus_sp1_armor_break")
        self.assertIsNotNone(a_sp1_break)
        self.assertEqual(a_sp1_break["t"], "\uE516")  # 碎裂胸甲破甲 PUA
        self.assertEqual(a_sp1_break["tc"], "EF4444") # 红色
        self.assertNotIn("#", a_sp1_break["tc"])

        # 3. SP1 攻击加成 (ID 2360)
        m_sp1_atk = stat_mods.get("optimus_sp1_atk_buff")
        self.assertIsNotNone(m_sp1_atk)
        self.assertEqual(m_sp1_atk["t"], "attack_buff")
        self.assertEqual(m_sp1_atk["m"], 0.20)
        self.assertEqual(m_sp1_atk["d"], 6.0)

        # 4. SP2 破甲 (ID 2337)
        m_sp2_break = stat_mods.get("optimus_sp2_armor_break")
        self.assertIsNotNone(m_sp2_break)
        self.assertEqual(m_sp2_break["m"], 0.35)
        self.assertEqual(m_sp2_break["d"], 6.0)

        # 5. SP3 破甲 (ID 2359) - 仅最后一击触发永久破甲 (d=-1.0)
        m_sp3_break = stat_mods.get("optimus_sp3_armor_break")
        self.assertIsNotNone(m_sp3_break)
        self.assertEqual(m_sp3_break["trs"], "level=Special3;dmgFlags=LastHit")
        self.assertEqual(m_sp3_break["m"], 0.35)
        self.assertEqual(m_sp3_break["d"], -1.0) # 永久破甲，无倒计时

        # 6. 觉醒技【突破口】(ID 2335): 对手破甲时暴击造成流血
        m_sig = stat_mods.get("optimus_sig_armor_break_bleed")
        self.assertIsNotNone(m_sig)
        self.assertEqual(m_sig["t"], "dmg_bleed")
        self.assertEqual(m_sig["tr"], ["onCrit"])
        self.assertEqual(m_sig["trs"], "opp.status=armor_break")
        self.assertEqual(m_sig["d"], 4.0)
        self.assertEqual(m_sig["ta"], "opponent")

        a_sig = appears.get("appr_optimus_sig_armor_break_bleed")
        self.assertIsNotNone(a_sig)
        self.assertEqual(a_sig["t"], "\uE401")
        self.assertEqual(a_sig["st"], "突破口")

        # 验证 bot_abilities 列表完整包含
        b_mods = bot_abilities(OPTIMUS_ID)
        self.assertIn("optimus_block_armor", b_mods)
        self.assertIn("optimus_sp1_armor_break", b_mods)
        self.assertIn("optimus_sp1_atk_buff", b_mods)
        self.assertIn("optimus_sp2_armor_break", b_mods)
        self.assertIn("optimus_sp3_armor_break", b_mods)
        self.assertIn("optimus_sig_armor_break_bleed", b_mods)

    def test_ultra_magnus_contract(self):
        """验证通天晓 SP 破甲与燃烧能力契约。"""
        stat_mods = build_stat_mods()
        appears = build_stat_mod_appears()

        # SP1 破甲 (ID 2865)
        m_sp1 = stat_mods.get("ultramagnus_sp1_armor_break")
        self.assertIsNotNone(m_sp1)
        self.assertEqual(m_sp1["t"], "armor_break")
        self.assertEqual(m_sp1["m"], 0.162)
        self.assertEqual(m_sp1["d"], 10.0)

        # SP2 第一击槌击破甲 (ID 2880)
        m_sp2_break = stat_mods.get("ultramagnus_sp2_armor_break")
        self.assertIsNotNone(m_sp2_break)
        self.assertEqual(m_sp2_break["trs"], "level=Special2;index=0")

        # SP2 第二下导弹燃烧 (ID 2875)
        m_sp2_burn = stat_mods.get("ultramagnus_sp2_burn")
        self.assertIsNotNone(m_sp2_burn)
        self.assertEqual(m_sp2_burn["trs"], "level=Special2;dmgFlags=LastHit")

        # SP3 第一击槌击破甲 (ID 2881)
        m_sp3_break = stat_mods.get("ultramagnus_sp3_armor_break")
        self.assertIsNotNone(m_sp3_break)
        self.assertEqual(m_sp3_break["trs"], "level=Special3;index=0")

        # SP3 后面几下导弹燃烧 (ID 2876)
        m_sp3_burn = stat_mods.get("ultramagnus_sp3_burn")
        self.assertIsNotNone(m_sp3_burn)
        self.assertEqual(m_sp3_burn["trs"], "level=Special3;index=1,2,3,4,5")

        # 重击燃烧 (ID 2874) - 65% 概率
        m_h_burn = stat_mods.get("ultramagnus_heavy_burn")
        self.assertIsNotNone(m_h_burn)
        self.assertEqual(m_h_burn["t"], "dmg_burn")
        self.assertEqual(m_h_burn["trs"], "level=Heavy")
        self.assertEqual(m_h_burn["c"], 0.65)
        self.assertEqual(m_h_burn["d"], 12.0)

        a_burn = appears.get("appr_ultramagnus_heavy_burn")
        self.assertIsNotNone(a_burn)
        self.assertEqual(a_burn["t"], "\uE41D")  # 燃烧 PUA
        self.assertEqual(a_burn["tc"], "FF6600")

        b_mods = bot_abilities(MAGNUS_ID)
        self.assertIn("ultramagnus_sp1_armor_break", b_mods)
        self.assertIn("ultramagnus_sp2_armor_break", b_mods)
        self.assertIn("ultramagnus_sp3_armor_break", b_mods)
        self.assertIn("ultramagnus_heavy_burn", b_mods)

    def test_grindor_contract(self):
        """验证碾碎器受创护甲与重击暴击燃烧契约。"""
        stat_mods = build_stat_mods()
        appears = build_stat_mod_appears()

        # 受创护甲 (ID 3056) - 8% 概率
        m_armor = stat_mods.get("grindor_hit_armor")
        self.assertIsNotNone(m_armor)
        self.assertEqual(m_armor["t"], "armor_up")
        self.assertEqual(m_armor["tr"], ["onPreDamage"])
        self.assertEqual(m_armor["c"], 0.08)
        self.assertEqual(m_armor["m"], 0.41)
        self.assertEqual(m_armor["d"], 6.0)

        a_armor = appears.get("appr_grindor_hit_armor")
        self.assertIsNotNone(a_armor)
        self.assertEqual(a_armor["t"], "\uE517")  # 完整胸甲 PUA
        self.assertEqual(a_armor["tc"], "29EBF4") # 官方电光青色

        # 重击暴击燃烧 (ID 3072)
        m_burn = stat_mods.get("grindor_heavy_crit_burn")
        self.assertIsNotNone(m_burn)
        self.assertEqual(m_burn["t"], "dmg_burn")
        self.assertEqual(m_burn["tr"], ["onCrit"])
        self.assertEqual(m_burn["trs"], "level=Heavy")
        self.assertEqual(m_burn["d"], 6.0)

        b_mods = bot_abilities(GRINDOR_ID)
        self.assertIn("grindor_hit_armor", b_mods)
        self.assertIn("grindor_heavy_crit_burn", b_mods)

    def test_buffs_config_and_set(self):
        """验证全局 Buff 库包含 armor_up, armor_break, attack_buff, dmg_burn。"""
        cfg = build_buffs_config()
        groups = cfg["groups"]
        self.assertIn("armor_up", groups)
        self.assertTrue(groups["armor_up"]["active_display"])
        self.assertIn("armor_break", groups)
        self.assertTrue(groups["armor_break"]["active_display"])
        self.assertIn("attack_buff", groups)
        self.assertTrue(groups["attack_buff"]["active_display"])
        self.assertIn("dmg_burn", groups)
        self.assertTrue(groups["dmg_burn"]["active_display"])

        b_set = build_buffs_set()
        global_buffs = b_set["globalBuffs"]
        self.assertIn("armor_up", global_buffs)
        self.assertIn("armor_break", global_buffs)
        self.assertIn("attack_buff", global_buffs)
        self.assertIn("dmg_burn", global_buffs)


if __name__ == "__main__":
    unittest.main()
