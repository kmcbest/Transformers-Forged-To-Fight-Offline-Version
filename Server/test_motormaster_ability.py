#!/usr/bin/env python3
"""
Unit Tests for Motormaster Combat Abilities (Unstoppable)
========================================================
测试目标:
1. 验证汽车大师 (motormaster_gs_voyager2015) 成功被能力总引擎加载并注册；
2. 验证前冲 (Dash) 霸体与 SP2 4秒霸体的修饰器及其光环特效修饰器正确生成；
3. 严格验证未添加用户未要求的其他技能（严禁超出范围）；
4. 验证契约属性 (tr, uit, 纯6位十六进制颜色代码, PUA 图标 \\uE915)；
5. 验证 build_buffs_config 和 build_buffs_set 包含 unstoppable 和 play_move。
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
import gamedata

BOT_ID = "motormaster_gs_voyager2015"


class TestMotormasterAbility(unittest.TestCase):
    def test_motormaster_registered(self):
        """验证汽车大师已在能力引擎中正确注册。"""
        registered = get_registered_bots()
        self.assertIn(BOT_ID, registered, "motormaster_gs_voyager2015 必须在已注册机器人列表中")

    def test_motormaster_mod_ids_scope(self):
        """严格验证汽车大师专属能力仅包含前冲霸体与 SP2 霸体，严禁包含其他能力。"""
        mod_ids = get_bot_mod_ids(BOT_ID)
        expected_custom_mods = [
            "motormaster_dash_unstoppable",
            "motormaster_sp2_unstoppable",
        ]
        self.assertEqual(
            sorted(mod_ids),
            sorted(expected_custom_mods),
            f"汽车大师专属能力集合必须严格为 {expected_custom_mods}，实际得到: {mod_ids}",
        )

    def test_motormaster_dash_unstoppable_contract(self):
        """验证前冲霸体修饰器的底层契约。"""
        stat_mods = build_stat_mods()
        dash_mod = stat_mods.get("motormaster_dash_unstoppable")
        self.assertIsNotNone(dash_mod, "必须存在 motormaster_dash_unstoppable 修饰器")
        self.assertEqual(dash_mod["t"], "unstoppable")
        self.assertEqual(dash_mod["tr"], ["onPlayerStateEnter"])
        self.assertEqual(dash_mod["trs"], "state=Dash")
        self.assertEqual(dash_mod["ta"], "self")
        self.assertEqual(dash_mod["mt"], "buff")
        self.assertGreaterEqual(dash_mod["d"], 0.5)

    def test_motormaster_sp2_unstoppable_contract(self):
        """验证 SP2 霸体修饰器的底层契约。"""
        stat_mods = build_stat_mods()
        sp2_mod = stat_mods.get("motormaster_sp2_unstoppable")
        self.assertIsNotNone(sp2_mod, "必须存在 motormaster_sp2_unstoppable 修饰器")
        self.assertEqual(sp2_mod["t"], "unstoppable")
        self.assertEqual(sp2_mod["tr"], ["onSpecial2Activate"])
        self.assertEqual(sp2_mod["ta"], "self")
        self.assertEqual(sp2_mod["mt"], "buff")
        self.assertEqual(sp2_mod["d"], 4.0, "SP2 不可阻挡必须持续 4.0 秒")

    def test_global_unstoppable_vfx_statmods(self):
        """验证全局系统修饰器 gb_unstoppfx 与 gb_unstoppfxrmv 正确装配。"""
        stat_mods = build_stat_mods()
        fx_mod = stat_mods.get("gb_unstoppfx")
        self.assertIsNotNone(fx_mod, "必须存在全局 gb_unstoppfx 修饰器")
        self.assertEqual(fx_mod["t"], "play_move")
        self.assertEqual(fx_mod["tm"], "status_unstoppable")
        self.assertEqual(fx_mod["tr"], ["onTypeActivate"])
        self.assertEqual(fx_mod["trs"], "type=unstoppable")
        self.assertEqual(fx_mod["d"], -1.0, "光环必须为常驻持续时间，直到被 gb_unstoppfxrmv 移除")

        rmv_mod = stat_mods.get("gb_unstoppfxrmv")
        self.assertIsNotNone(rmv_mod, "必须存在全局 gb_unstoppfxrmv 修饰器")
        self.assertEqual(rmv_mod["t"], "remove")
        self.assertEqual(rmv_mod["tm"], "gb_unstoppfx")
        self.assertEqual(rmv_mod["tr"], ["onTypeExpiry"])
        self.assertEqual(rmv_mod["trs"], "type=unstoppable")

    def test_motormaster_appears(self):
        """验证汽车大师霸体外观表现与 PUA 图标契约。"""
        appears = build_stat_mod_appears()
        appr_dash = appears.get("appr_motormaster_dash_unstoppable")
        self.assertIsNotNone(appr_dash)
        self.assertEqual(appr_dash["t"], "\uE915", "PUA 图标必须为不可阻挡图标 0xe915")
        self.assertFalse(appr_dash["tc"].startswith("#"), "颜色代码严禁带 '#' 前缀")
        self.assertEqual(len(appr_dash["tc"]), 6, "颜色代码必须为纯 6 位十六进制")

        appr_sp2 = appears.get("appr_motormaster_sp2_unstoppable")
        self.assertIsNotNone(appr_sp2)
        self.assertEqual(appr_sp2["t"], "\uE915")
        self.assertEqual(appr_sp2["st"], "ID_STAT_UNSTOPPABLE_HUD")
        self.assertFalse(appr_sp2["tc"].startswith("#"))
        self.assertEqual(len(appr_sp2["tc"]), 6)

    def test_buffs_config_and_set(self):
        """验证 buffs_config 与 buffs_set 包含了不可阻挡与动作播放模板。"""
        cfg = build_buffs_config()
        self.assertIn("unstoppable", cfg["groups"])
        self.assertTrue(cfg["groups"]["unstoppable"]["active_display"])
        self.assertFalse(cfg["groups"]["unstoppable"]["stackable"])

        self.assertIn("play_move", cfg["groups"])
        self.assertFalse(cfg["groups"]["play_move"]["active_display"])

        b_set = build_buffs_set()
        self.assertIn("unstoppable", b_set["globalBuffs"])
        self.assertEqual(b_set["globalBuffs"]["unstoppable"]["buffType"], "unstoppable")
        self.assertIn("play_move", b_set["globalBuffs"])
        self.assertEqual(b_set["globalBuffs"]["play_move"]["buffType"], "play_move")

    def test_gamedata_bot_abilities_integration(self):
        """验证 gamedata.bot_abilities 与 abilities.bot_abilities 产出完整一致的能力列表。"""
        mods = gamedata.bot_abilities(BOT_ID)
        # 必须包含 3 个 SP 呼出
        for lvl in (1, 2, 3):
            self.assertIn(f"sp_callout_{BOT_ID}_{lvl}", mods)
        # 必须包含汽车大师专属霸体能力
        self.assertIn("motormaster_dash_unstoppable", mods)
        self.assertIn("motormaster_sp2_unstoppable", mods)
        # 必须包含 UI 基础展示能力
        self.assertIn(f"ability_{BOT_ID}_0", mods)
        self.assertIn(f"ability_{BOT_ID}_1", mods)


if __name__ == "__main__":
    unittest.main()
