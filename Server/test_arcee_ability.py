#!/usr/bin/env python3
"""
Unit test for Arcee's official Headshot Bleed ability integration.
Validates the single source of truth, wire schemas, list accessor safety,
and payload integration across Server/abilities.py and Server/gamedata.py.
"""
import io
import json
import os
import sys
import unittest

# Force stdout to UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import abilities
import gamedata


class TestArceeAbility(unittest.TestCase):
    def test_single_source_of_truth_bot_abilities(self):
        """Verify bot_abilities grants official abilities to Arcee."""
        expected_abilities = [
            "arcee_headshot_direct",
            "arcee_headshot_dot",
            "arcee_headshot_rush",
            "arcee_s2_bleed",
        ]
        self.assertEqual(
            gamedata.bot_abilities("arcee_gs_deluxe2014"),
            expected_abilities,
        )
        self.assertEqual(
            abilities.bot_abilities("arcee_gs_deluxe2014"),
            expected_abilities,
        )
        # Other bots must not have Arcee's ability
        self.assertEqual(gamedata.bot_abilities("optimusprime_cin_tf"), [])
        self.assertEqual(gamedata.bot_abilities("megatron_gs_leader2015"), [])

    def test_buffs_config_and_set(self):
        """Verify globalBuffs, groups, and groupings are properly formatted for Damage_BuffEffect."""
        cfg = gamedata.build_buffs_config()
        self.assertIn("groups", cfg)
        self.assertIn("groupings", cfg)
        self.assertIn("dmg_bleed", cfg["groups"])
        self.assertTrue(cfg["groups"]["dmg_bleed"]["stackable"])
        self.assertTrue(cfg["groups"]["dmg_bleed"]["active_display"])
        self.assertFalse(cfg["groups"]["dmg_direct"]["active_display"])

        buffs_set = gamedata.build_buffs_set()
        self.assertIn("globalBuffs", buffs_set)
        self.assertIn("dmg_bleed", buffs_set["globalBuffs"])

        bleed = buffs_set["globalBuffs"]["dmg_bleed"]
        self.assertEqual(bleed["buffType"], "damage")
        self.assertEqual(bleed["group"], "dmg_bleed")
        self.assertEqual(bleed["p"], {"damage_type": "bleed"})
        self.assertTrue(bleed["hasDuration"])

    def test_stat_modifier_schema_and_types(self):
        """Verify critical type rules: tr, uit, and a MUST be lists!"""
        mods = gamedata.build_stat_modifiers()
        for k in ["arcee_headshot_direct", "arcee_headshot_dot", "arcee_headshot_rush", "arcee_s2_bleed"]:
            self.assertIn(k, mods)
            mod = mods[k]
            # Accessor types: lists required by client IL2CPP
            self.assertIsInstance(mod["tr"], list)
            self.assertIsInstance(mod["uit"], list)
            self.assertIsInstance(mod["a"], list)
            self.assertEqual(mod["ta"], "opponent")
            if k == "arcee_headshot_direct":
                self.assertEqual(mod["mt"], "passive")
                self.assertEqual(mod["a"], [])
            else:
                self.assertEqual(mod["mt"], "debuff")
                self.assertEqual(mod["a"], ["appr_arcee_bleed"])

        # Headshot direct: instant 60% atk (2091), d=0.5, c=0.5, on ranged / S1 / S3 crit
        d_mod = mods["arcee_headshot_direct"]
        self.assertEqual(d_mod["m"], 2091.0)
        self.assertEqual(d_mod["d"], 0.5)
        self.assertEqual(d_mod["c"], 0.5)
        self.assertIn("onRangedHit", d_mod["tr"])
        self.assertIn("onSpecial1Hit", d_mod["tr"])
        self.assertIn("onSpecial3Hit", d_mod["tr"])

        # Headshot DOT: 60% atk over 3s, d=3.0, c=0.5, on ranged / S1 crit
        dot_mod = mods["arcee_headshot_dot"]
        self.assertEqual(dot_mod["m"], 2091.0)
        self.assertEqual(dot_mod["d"], 3.0)
        self.assertEqual(dot_mod["c"], 0.5)

        # Headshot rush: extra 50% chance when enemy is dashing
        rush_mod = mods["arcee_headshot_rush"]
        self.assertEqual(rush_mod["m"], 2091.0)
        self.assertEqual(rush_mod["d"], 3.0)
        self.assertEqual(rush_mod["c"], 0.5)
        self.assertEqual(rush_mod["trs"], "opponent:state=Dashing")

        # S2 Bleed: 108% atk (3764) over 4s, d=4.0, c=1.0, on S2 crit
        s2_mod = mods["arcee_s2_bleed"]
        self.assertEqual(s2_mod["m"], 3764.0)
        self.assertEqual(s2_mod["d"], 4.0)
        self.assertEqual(s2_mod["c"], 1.0)
        self.assertIn("onSpecial2Hit", s2_mod["tr"])

    def test_stat_mod_appears_and_unicode_glyph(self):
        """Verify statModAppears defines real PUA codepoint \uE401 (bleed) and raw 6-digit hex."""
        appears = gamedata.build_stat_mod_appears()
        for k in ["appr_arcee_headshot", "appr_arcee_bleed"]:
            self.assertIn(k, appears)
            app = appears[k]
            self.assertEqual(app["t"], "\uE401")
            self.assertEqual(app["tc"], "FF0000")  # Raw hex without '#' to prevent RGB shift to yellow!

    def test_four_builders_carry_abilities(self):
        """Verify the 4 critical builders all inject bot_abilities correctly."""
        expected = [
            "arcee_headshot_direct",
            "arcee_headshot_dot",
            "arcee_headshot_rush",
            "arcee_s2_bleed",
        ]
        # 1. build_hero_base
        base = gamedata.build_hero_base("arcee_gs_deluxe2014")
        self.assertEqual(base["stat_mods"], expected)

        # 2. build_hero_entry
        entry = gamedata.build_hero_entry("arcee_gs_deluxe2014")
        self.assertEqual(entry["stat_mods"], expected)

        # 3. build_base_hero_details
        details = gamedata.build_base_hero_details([{"bid": "arcee_gs_deluxe2014"}])
        self.assertEqual(details[0]["stat_mods"], expected)

        # 4. quest_team (CRITICAL for fight execution!)
        prog = gamedata.build_quest_progression(team=["arcee_gs_deluxe2014"])
        user_team = prog["users"][gamedata.LOCAL_UID]["team"]
        self.assertIn("arcee_gs_deluxe2014", user_team)
        self.assertEqual(
            user_team["arcee_gs_deluxe2014"]["stat_mods"],
            expected,
        )

    def test_saved_json_responses(self):
        """Verify the serialized JSON response files on disk contain valid abilities and Unicode."""
        resp_dir = gamedata.RESP_DIR

        # Check GET__bcg_getLoginData.json
        login_path = os.path.join(resp_dir, "GET__bcg_getLoginData.json")
        with open(login_path, "r", encoding="utf-8") as f:
            login_data = json.load(f)["result"]
        self.assertIn("arcee_headshot_dot", login_data["statMods"])
        self.assertIn("appr_arcee_bleed", login_data["statModAppears"])
        self.assertEqual(login_data["statModAppears"]["appr_arcee_bleed"]["t"], "\uE401")

        # Check GET__account_data.json
        account_path = os.path.join(resp_dir, "GET__account_data.json")
        with open(account_path, "r", encoding="utf-8") as f:
            account_data = json.load(f)["result"]
        self.assertIn("buffs_config", account_data)
        self.assertIn("buffs_set", account_data)
        self.assertIn("dmg_bleed", account_data["buffs_set"]["globalBuffs"])


if __name__ == "__main__":
    unittest.main()
