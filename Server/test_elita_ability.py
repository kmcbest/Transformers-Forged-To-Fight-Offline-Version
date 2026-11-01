#!/usr/bin/env python3
"""
Unit test for Elita-1 (艾丽塔) official abilities integration.
Validates single source of truth, statmods, appearances, and IL2CPP data contracts.
"""
import io
import os
import sys
import unittest

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import abilities
import gamedata
from abilities.bots.elita_one import build_elita_abilities


class TestElitaAbility(unittest.TestCase):
    def test_elita_abilities_generation(self):
        """Verify build_elita_abilities generates all required statmods and adheres to contracts."""
        mods, appears, buffs = build_elita_abilities(38400.0, 2780.0)

        # 1. Check all 14 priority mechanics exist
        expected_keys = [
            "elita_sp1_armor_break",
            "elita_sp1_armor_break_braw",
            "elita_sp1_power_burn",
            "elita_sp2_nullify",
            "elita_sp2_shock",
            "elita_sp3_bleed",
            "elita_sp3_tactical_lockdown",
            "elita_tactical_insight_evade",
            "elita_tactical_insight_melee_buff",
            "elita_counter_pouch_buff",
            "elita_counter_stun",
            "elita_counter_atk_debuff",
            "elita_joint_aim_pierce",
            "elita_joint_aim_refresh",
            "elita_ranged_crit_armor_break",
            "elita_commanders_presence",
            "elita_sig_flame_atk_50",
            "elita_sig_flame_crit_50",
            "elita_sig_flame_armor_25",
            "elita_sig_flame_interrupt_stun",
            "elita_sig_flame_interrupt_stun_braw",
            "elita_synergy_eternal_bond_shield",
            "elita_synergy_sisters_crit",
            "elita_synergy_sisters_heavy",
        ]
        for k in expected_keys:
            self.assertIn(k, mods, f"Missing statmod: {k}")

        # 2. Check shock and bleed damages and tick safety
        shock = mods["elita_sp2_shock"]
        self.assertEqual(shock["d"], 10.0)
        self.assertEqual(shock["m"], 2780.0)
        self.assertGreaterEqual(shock["m"] / (shock["d"] * 2.0), 1.0)

        bleed = mods["elita_sp3_bleed"]
        self.assertEqual(bleed["d"], 6.0)
        self.assertEqual(bleed["m"], 3336.0)
        self.assertGreaterEqual(bleed["m"] / (bleed["d"] * 2.0), 1.0)

        # 3. Check colors in appearances (no '#' prefix)
        for appr_id, appr in appears.items():
            for c_field in ("tc", "gt", "gb"):
                if c_field in appr and appr[c_field]:
                    color = appr[c_field]
                    self.assertFalse(color.startswith("#"), f"Color in {appr_id}.{c_field} must not start with '#'")
                    self.assertEqual(len(color), 6, f"Color in {appr_id}.{c_field} must be 6 hex characters")

    def test_gamedata_integration(self):
        """Verify gamedata integrates elita_one_gs correctly."""
        bot_list = gamedata.bot_abilities("elita_one_gs")
        self.assertIn("elita_sp1_armor_break", bot_list)
        self.assertIn("elita_sp2_shock", bot_list)
        self.assertIn("elita_sp3_bleed", bot_list)
        self.assertIn("elita_tactical_insight_evade", bot_list)
        self.assertIn("elita_sig_flame_atk_50", bot_list)
        self.assertIn("elita_synergy_eternal_bond_shield", bot_list)


if __name__ == "__main__":
    unittest.main()
