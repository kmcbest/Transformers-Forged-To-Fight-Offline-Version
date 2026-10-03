#!/usr/bin/env python3
"""
Unit tests for the Universal Special Attack (SP1/SP2/SP3) Callout Text System.
=============================================================================
Tests:
  1. Universal registration for all 78 bots in the official roster.
  2. SP1, SP2, SP3 trigger binding to onSpecial1Activate, onSpecial2Activate, onSpecial3Activate.
  3. Appearance mapping to real localization keys (ID_SPECIAL_ATTACK_...).
  4. HUD configuration: active_display is False (suppresses buff grid icons under health bar).
  5. Target is 'self' so Player 0 displays on left, Player 1 displays on right.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import abilities
import gamedata


class TestUniversalSpCallout(unittest.TestCase):
    def test_roster_full_coverage(self):
        """All 78 bots in ROSTER must have SP callout mappings."""
        for bid in gamedata.ROSTER:
            mods = abilities.bot_abilities(bid)
            for lvl in (1, 2, 3):
                expected_mod = f"sp_callout_{bid}_{lvl}"
                self.assertIn(
                    expected_mod,
                    mods,
                    f"Bot {bid} missing {expected_mod}",
                )

    def test_buffs_config_suppresses_grid_icon(self):
        """sp_callout must have active_display=False so it only triggers Callout text without health bar icon."""
        cfg = abilities.build_buffs_config()
        self.assertIn("sp_callout", cfg["groups"])
        sp_group = cfg["groups"]["sp_callout"]
        self.assertTrue(sp_group["stackable"])
        self.assertFalse(sp_group["active_display"])

    def test_buffs_set_duration_one_second(self):
        """sp_callout global buff must have duration of 1.0 second."""
        buffs_set = abilities.build_buffs_set()
        self.assertIn("sp_callout", buffs_set["globalBuffs"])
        sp_buff = buffs_set["globalBuffs"]["sp_callout"]
        self.assertTrue(sp_buff["hasDuration"])
        self.assertEqual(sp_buff["time"]["amount"], 1.0)
        self.assertEqual(sp_buff["group"], "sp_callout")

    def test_stat_modifiers_triggers_and_targets(self):
        """Verify triggers (onSpecial{lvl}Activate) and target (self)."""
        stat_mods = abilities.build_stat_modifiers()
        for bid in gamedata.ROSTER:
            for lvl in (1, 2, 3):
                mod_id = f"sp_callout_{bid}_{lvl}"
                self.assertIn(mod_id, stat_mods)
                mod = stat_mods[mod_id]
                self.assertEqual(mod["t"], "sp_callout")
                self.assertEqual(mod["tr"], [f"onSpecial{lvl}Activate"])
                self.assertEqual(mod["uit"], [f"onSpecial{lvl}Activate"])
                self.assertEqual(mod["ta"], "self")
                self.assertEqual(mod["c"], 1.0)
                self.assertEqual(mod["d"], 1.0)
                self.assertEqual(mod["a"], [f"appr_sp_{bid}_{lvl}"])

    def test_stat_mod_appears_localization_and_colors(self):
        """Verify appearance references valid ID_SPECIAL_ATTACK_* keys and valid 6-hex colors."""
        appears = abilities.build_stat_mod_appears()
        for bid in gamedata.ROSTER:
            for lvl in (1, 2, 3):
                appr_id = f"appr_sp_{bid}_{lvl}"
                self.assertIn(appr_id, appears)
                appr = appears[appr_id]
                st_key = appr["st"]
                self.assertTrue(
                    st_key.startswith("ID_SPECIAL_ATTACK_"),
                    f"Invalid loc key '{st_key}' in {appr_id}",
                )
                self.assertNotIn("DESCRIPTION", st_key)
                self.assertEqual(len(appr["tc"]), 6)
                self.assertFalse(appr["tc"].startswith("#"))
                self.assertEqual(len(appr["gt"]), 6)
                self.assertEqual(len(appr["gb"]), 6)


if __name__ == "__main__":
    unittest.main()
