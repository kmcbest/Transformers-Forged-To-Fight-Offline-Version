#!/usr/bin/env python3
"""
Unit tests for the 20 priority abilities across 8 bots:
- 电影铁皮 (ironhide_cin_rotf)
- 红蜘蛛 (fte_stars_gs_t3)
- 恐龙勇士 (dinobot_bw_kabam)
- 巨蝎勇士 (scorponok_bw_kabam)
- 横炮 (sideswipe_gs)
- 喷气机 (ramjet_gs_deluxe2008)
- 搅拌者 (mixmaster_cin_rotf)
- 黄蜂勇士 (waspinator_gs_deluxe)
"""

import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "Server"))

import abilities
import gamedata


class TestPriorityAbilities(unittest.TestCase):
    def test_all_eight_bots_registered(self):
        registered = abilities.get_registered_bots()
        expected = [
            "ironhide_cin_rotf",
            "fte_stars_gs_t3",
            "dinobot_bw_kabam",
            "scorponok_bw_kabam",
            "sideswipe_gs",
            "ramjet_gs_deluxe2008",
            "mixmaster_cin_rotf",
            "waspinator_gs_deluxe",
            "prowl_gs_deluxe2016",
        ]
        for bid in expected:
            self.assertIn(bid, registered, f"Bot {bid} should be registered in ability registry")

    def test_prowl_abilities(self):
        mod_ids = abilities.bot_abilities("prowl_gs_deluxe2016")
        expected = [
            "prowl_s1_power_burn",
            "prowl_s2_ranged_boost",
            "prowl_s3_power_lock",
            "prowl_melee_charge",
            "prowl_passive_melee_buff",
            "prowl_ranged_stun",
        ]
        for m in expected:
            self.assertIn(m, mod_ids)

    def test_ironhide_abilities(self):
        mod_ids = abilities.bot_abilities("ironhide_cin_rotf")
        expected_mods = [
            "ironhide_missile_burn",
            "ironhide_missile_burn_stack",
            "ironhide_missile_crit",
            "ironhide_s2_crit_dmg",
            "ironhide_s3_burn",
        ]
        for m in expected_mods:
            self.assertIn(m, mod_ids)

    def test_starscream_abilities(self):
        mod_ids = abilities.bot_abilities("fte_stars_gs_t3")
        self.assertIn("starscream_heavy_burn", mod_ids)

    def test_dinobot_abilities(self):
        mod_ids = abilities.bot_abilities("dinobot_bw_kabam")
        self.assertIn("dinobot_heavy_crit_bleed", mod_ids)

    def test_scorponok_abilities(self):
        mod_ids = abilities.bot_abilities("scorponok_bw_kabam")
        self.assertIn("scorponok_melee_crit_bleed", mod_ids)

    def test_sideswipe_abilities(self):
        mod_ids = abilities.bot_abilities("sideswipe_gs")
        expected = [
            "sideswipe_s1_crit_rate",
            "sideswipe_s1_stun",
            "sideswipe_s2_burn",
            "sideswipe_s3_burn",
            "sideswipe_s3_nullify",
        ]
        for m in expected:
            self.assertIn(m, mod_ids)

    def test_ramjet_abilities(self):
        mod_ids = abilities.bot_abilities("ramjet_gs_deluxe2008")
        expected = [
            "ramjet_heavy_burn_stun",
            "ramjet_heavy_unstoppable",
            "ramjet_s1_burn",
            "ramjet_s2_burn",
            "ramjet_s3_stun_opp",
            "ramjet_s3_stun_self",
        ]
        for m in expected:
            self.assertIn(m, mod_ids)

    def test_mixmaster_abilities(self):
        mod_ids = abilities.bot_abilities("mixmaster_cin_rotf")
        expected = [
            "mixmaster_s2_burn",
            "mixmaster_s3_burn",
        ]
        for m in expected:
            self.assertIn(m, mod_ids)

    def test_waspinator_abilities(self):
        mod_ids = abilities.bot_abilities("waspinator_gs_deluxe")
        self.assertIn("waspinator_s3_burn", mod_ids)

    def test_stat_mods_and_appears_validity(self):
        all_mods = abilities.build_stat_mods()
        all_appears = abilities.build_stat_mod_appears()

        all_target_mods = [
            "ironhide_missile_burn",
            "ironhide_missile_burn_stack",
            "ironhide_missile_crit",
            "ironhide_s2_crit_dmg",
            "ironhide_s3_burn",
            "starscream_heavy_burn",
            "dinobot_heavy_crit_bleed",
            "scorponok_melee_crit_bleed",
            "sideswipe_s1_crit_rate",
            "sideswipe_s1_stun",
            "sideswipe_s2_burn",
            "sideswipe_s3_burn",
            "sideswipe_s3_nullify",
            "ramjet_heavy_burn_stun",
            "ramjet_heavy_unstoppable",
            "ramjet_s1_burn",
            "ramjet_s2_burn",
            "ramjet_s3_stun_opp",
            "ramjet_s3_stun_self",
            "mixmaster_s2_burn",
            "mixmaster_s3_burn",
            "waspinator_s3_burn",
            "prowl_s1_power_burn",
            "prowl_s2_ranged_boost",
            "prowl_s3_power_lock",
            "prowl_melee_charge",
            "prowl_passive_melee_buff",
            "prowl_ranged_stun",
        ]

        for mid in all_target_mods:
            self.assertIn(mid, all_mods, f"StatMod {mid} must be in build_stat_mods()")
            mod = all_mods[mid]
            self.assertTrue(isinstance(mod["tr"], list), "tr must be list")
            self.assertTrue(isinstance(mod["uit"], list), "uit must be list")
            self.assertTrue(isinstance(mod["a"], list), "a must be list")

            # Check appearances
            for aid in mod["a"]:
                self.assertIn(aid, all_appears, f"Appearance {aid} must be in build_stat_mod_appears()")
                appr = all_appears[aid]
                for ckey in ("tc", "gt", "gb", "bc"):
                    if ckey in appr and appr[ckey]:
                        color = appr[ckey]
                        self.assertFalse(color.startswith("#"), f"Color {ckey} cannot start with #: {color}")
                        self.assertEqual(len(color), 6, f"Color {ckey} must be 6 hex digits: {color}")

        # Check signature appearance exists
        self.assertIn("appr_prowl_sig_good_cop", all_appears)

    def test_gamedata_integration(self):
        # Ensure gamedata builds without error
        stat_mods = gamedata.build_stat_modifiers()
        buffs_set = gamedata.build_buffs_set()
        self.assertIn("crit_damage", buffs_set["globalBuffs"])

        # Check that ironhide has stat_mods in hero entry
        hero_data = gamedata.build_hero_entry("ironhide_cin_rotf", 5, 50)
        self.assertIn("stat_mods", hero_data)
        self.assertTrue(len(hero_data["stat_mods"]) > 0)

        # Check prowl hero entry
        prowl_data = gamedata.build_hero_entry("prowl_gs_deluxe2016", 5, 50)
        self.assertIn("stat_mods", prowl_data)
        self.assertIn("prowl_s1_power_burn", prowl_data["stat_mods"])
        self.assertIn("prowl_s2_ranged_boost", prowl_data["stat_mods"])
        self.assertIn("prowl_s3_power_lock", prowl_data["stat_mods"])
        self.assertIn("prowl_melee_charge", prowl_data["stat_mods"])
        self.assertIn("prowl_passive_melee_buff", prowl_data["stat_mods"])
        self.assertIn("prowl_ranged_stun", prowl_data["stat_mods"])


if __name__ == "__main__":
    unittest.main()
