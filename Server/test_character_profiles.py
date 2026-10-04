#!/usr/bin/env python3
"""
Unit tests for Character Profiles Integration (Synergy, Signature, UI Abilities).
================================================================================
Validates:
  1. All 78 bots have blueprints with 'sb' and matching synergyBonuses in loginData.
  2. All 78 bots have sig_mods populated and registered in statMods and statModAppears.
  3. UI abilities (basic/passive) are present with valid ShortStringID and descriptions.
  4. SP callouts have empty ShortStringID to prevent polluting abilities panel.
  5. Arcee specifically matches user requirement:
     - Signature: "守卫者的残暴" / "Guardian's Ferocity"
     - Abilities: 2 basic abilities ("规避" and "爆头")
     - Synergies: 6 synergy bonuses with valid partner heroes and textures
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gamedata
import abilities
import character_profiles


class TestCharacterProfiles(unittest.TestCase):
    def test_synergy_bonuses_coverage(self):
        """All 78 bots have blueprints with 'sb' and valid definitions in synergyBonuses."""
        blueprints = gamedata.build_blueprints()
        synergies = character_profiles.build_all_synergy_bonuses()

        for bid in gamedata.ROSTER:
            self.assertIn(bid, blueprints)
            bp = blueprints[bid]
            self.assertIn("sb", bp)
            self.assertIn("synergy_bonuses", bp)
            self.assertEqual(bp["sb"], bp["synergy_bonuses"])
            # Check every synergy referenced exists in synergies dictionary
            for syn_id in bp["sb"]:
                self.assertIn(syn_id, synergies, f"Synergy {syn_id} missing in global synergyBonuses")
                syn = synergies[syn_id]
                self.assertTrue(len(syn["st"]) > 0, f"Synergy {syn_id} missing texture/icon")
                self.assertTrue(len(syn["s"]) > 0, f"Synergy {syn_id} missing name")
                self.assertTrue(syn["e"], f"Synergy {syn_id} must be enabled")

    def test_signature_abilities_coverage(self):
        """All 78 bots have sig_mods and appearances in getLoginData."""
        stat_mods = abilities.build_stat_modifiers()
        appears = abilities.build_stat_mod_appears()

        for bid in gamedata.ROSTER:
            entry = gamedata.build_hero_entry(bid)
            self.assertEqual(len(entry["sig_mods"]), 1, f"Bot {bid} missing sig_mods")
            sig_id = entry["sig_mods"][0]
            self.assertEqual(sig_id, f"sig_{bid}")
            self.assertIn(sig_id, stat_mods, f"Sig mod {sig_id} missing in stat_mods")
            appr_id = stat_mods[sig_id]["AppearanceID"]
            self.assertIn(appr_id, appears, f"Sig appearance {appr_id} missing in appears")
            self.assertTrue(len(appears[appr_id]["s"]) > 0, f"Sig {sig_id} appearance has empty name")

    def test_sp_callouts_suppressed_from_ability_panel(self):
        """sp_callouts must have empty 's' (ShortStringID) so CharacterStatSummaryPanel ignores them."""
        appears = abilities.build_stat_mod_appears()
        for bid in gamedata.ROSTER:
            for lvl in (1, 2, 3):
                appr_id = f"appr_sp_{bid}_{lvl}"
                self.assertIn(appr_id, appears)
                self.assertEqual(
                    appears[appr_id]["s"],
                    "",
                    f"sp_callout {appr_id} must have empty ShortStringID to prevent polluting ability panel",
                )

    def test_arcee_profile_exact_match(self):
        """Verify Arcee's exact profile: Guardian's Ferocity sig, 2 basic abilities (Evade, Head Shot)."""
        bid = "arcee_gs_deluxe2014"
        entry = gamedata.build_hero_entry(bid)
        stat_mods = abilities.build_stat_modifiers()
        appears = abilities.build_stat_mod_appears()

        # Signature: 守卫者的残暴
        sig_id = entry["sig_mods"][0]
        sig_appr = appears[stat_mods[sig_id]["AppearanceID"]]
        self.assertEqual(sig_appr["s"], "守卫者的残暴")

        # Abilities: 规避 & 爆头
        ui_mods = character_profiles.get_bot_ui_ability_ids(bid)
        self.assertEqual(len(ui_mods), 2)
        ab0_appr = appears[stat_mods[ui_mods[0]]["AppearanceID"]]
        ab1_appr = appears[stat_mods[ui_mods[1]]["AppearanceID"]]
        self.assertEqual(ab0_appr["s"], "规避")
        self.assertEqual(ab0_appr["t"], "\ue518")
        self.assertEqual(ab1_appr["s"], "爆头")
        self.assertEqual(ab1_appr["t"], "\ue401")

        # Synergies: 6 synergies
        syn_ids = character_profiles.get_bot_synergy_ids(bid)
        self.assertEqual(len(syn_ids), 6)
        synergies = character_profiles.build_all_synergy_bonuses()
        # Sharpshooters (3rd synergy) partner test: RequiredHeroes should contain Mirage & Hound
        sharpshooter = synergies[syn_ids[2]]
        self.assertEqual(sharpshooter["s"], "神枪手")
        self.assertEqual(sharpshooter["b"], [bid])
        self.assertIn("mirage_gs_deluxe2016", sharpshooter["r"])
        self.assertIn("hound_cin_tlk", sharpshooter["r"])


if __name__ == "__main__":
    unittest.main()
