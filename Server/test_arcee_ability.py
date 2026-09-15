#!/usr/bin/env python3
"""
Unit test for Arcee's official Headshot Bleed ability integration.
Validates the single source of truth, wire schemas, list accessor safety,
and payload integration.
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

import gamedata


class TestArceeAbility(unittest.TestCase):
    def test_single_source_of_truth_bot_abilities(self):
        """Verify bot_abilities only grants headshot bleed to Arcee."""
        self.assertEqual(
            gamedata.bot_abilities("arcee_gs_deluxe2014"),
            ["arcee_headshot_bleed"],
        )
        # Other bots must not have Arcee's ability
        self.assertEqual(gamedata.bot_abilities("optimusprime_cin_tf"), [])
        self.assertEqual(gamedata.bot_abilities("megatron_gs_leader2015"), [])

    def test_buffs_config_and_set(self):
        """Verify globalBuffs and groupings are properly formatted for Damage_BuffEffect."""
        cfg = gamedata.build_buffs_config()
        self.assertIn("groupings", cfg)
        self.assertIn("dmg_bleed", cfg["groupings"])
        self.assertTrue(cfg["groupings"]["dmg_bleed"]["stackable"])
        self.assertTrue(cfg["groupings"]["dmg_bleed"]["active_display"])

        buffs_set = gamedata.build_buffs_set()
        self.assertIn("globalBuffs", buffs_set)
        self.assertIn("dmg_bleed", buffs_set["globalBuffs"])

        bleed = buffs_set["globalBuffs"]["dmg_bleed"]
        self.assertEqual(bleed["buffType"], "damage")
        self.assertEqual(bleed["group"], "dmg_bleed")
        self.assertEqual(bleed["p"], {"damage_type": "bleed"})
        self.assertTrue(bleed["hasDuration"])
        self.assertEqual(bleed["time"]["amount"], 3.0)
        self.assertEqual(bleed["value"], 0.6)

    def test_stat_modifier_schema_and_types(self):
        """Verify critical type rules: tr, uit, and a MUST be lists!"""
        mods = gamedata.build_stat_modifiers()
        self.assertIn("arcee_headshot_bleed", mods)

        mod = mods["arcee_headshot_bleed"]
        # Wire 't' must match globalBuffs id and start with 'dmg_' for Damage_BuffEffect
        self.assertEqual(mod["t"], "dmg_bleed")
        self.assertTrue(mod["t"].startswith("dmg_"))

        # Accessor types: lists required by client IL2CPP
        self.assertIsInstance(mod["tr"], list)
        self.assertIn("onHit", mod["tr"])
        self.assertIsInstance(mod["uit"], list)
        self.assertIn("onHit", mod["uit"])
        self.assertIsInstance(mod["a"], list)
        self.assertEqual(mod["a"], ["arcee_headshot_bleed"])

        # Target and magnitude
        self.assertEqual(mod["ta"], "opponent")
        self.assertEqual(mod["mt"], "debuff")
        self.assertEqual(mod["c"], 1.0)
        self.assertEqual(mod["m"], 0.6)
        self.assertEqual(mod["d"], 3.0)
        self.assertEqual(mod["st"], 1)

    def test_stat_mod_appears_and_unicode_glyph(self):
        """Verify statModAppears defines real PUA codepoint \uE402 (bleed)."""
        appears = gamedata.build_stat_mod_appears()
        self.assertIn("arcee_headshot_bleed", appears)
        app = appears["arcee_headshot_bleed"]
        self.assertEqual(app["t"], "\uE402")
        self.assertEqual(app["st"], "BLEED")

    def test_four_builders_carry_abilities(self):
        """Verify the 4 critical builders all inject bot_abilities correctly."""
        # 1. build_hero_base
        base = gamedata.build_hero_base("arcee_gs_deluxe2014")
        self.assertEqual(base["stat_mods"], ["arcee_headshot_bleed"])

        # 2. build_hero_entry
        entry = gamedata.build_hero_entry("arcee_gs_deluxe2014")
        self.assertEqual(entry["stat_mods"], ["arcee_headshot_bleed"])

        # 3. build_base_hero_details
        details = gamedata.build_base_hero_details([{"bid": "arcee_gs_deluxe2014"}])
        self.assertEqual(details[0]["stat_mods"], ["arcee_headshot_bleed"])

        # 4. quest_team (CRITICAL for fight execution!)
        prog = gamedata.build_quest_progression(team=["arcee_gs_deluxe2014"])
        user_team = prog["users"][gamedata.LOCAL_UID]["team"]
        self.assertIn("arcee_gs_deluxe2014", user_team)
        self.assertEqual(
            user_team["arcee_gs_deluxe2014"]["stat_mods"],
            ["arcee_headshot_bleed"],
        )

    def test_saved_json_responses(self):
        """Verify the serialized JSON response files on disk contain valid abilities and Unicode."""
        resp_dir = gamedata.RESP_DIR

        # Check GET__bcg_getLoginData.json
        login_path = os.path.join(resp_dir, "GET__bcg_getLoginData.json")
        with open(login_path, "r", encoding="utf-8") as f:
            login_data = json.load(f)["result"]
        self.assertIn("arcee_headshot_bleed", login_data["statMods"])
        self.assertIn("arcee_headshot_bleed", login_data["statModAppears"])
        self.assertEqual(login_data["statModAppears"]["arcee_headshot_bleed"]["t"], "\uE402")

        # Check GET__account_data.json
        account_path = os.path.join(resp_dir, "GET__account_data.json")
        with open(account_path, "r", encoding="utf-8") as f:
            account_data = json.load(f)["result"]
        self.assertIn("buffs_config", account_data)
        self.assertIn("buffs_set", account_data)
        self.assertIn("dmg_bleed", account_data["buffs_set"]["globalBuffs"])


if __name__ == "__main__":
    unittest.main()
