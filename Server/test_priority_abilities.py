#!/usr/bin/env python3
"""
Unit tests for all 19 priority bots and 72 abilities from the Upstash live breakdown:
- 钢锁 (grimlock_gs_mp08): 7 abilities
- 电影大黄蜂 (bumblebee_cin_dotm): 6 abilities
- 狂暴/野牛 (tantrum_gs_kabam): 5 abilities
- 惊天雷 (thundercracker_gs_leader2015): 5 abilities
- 威震天 (megatron_gs_leader2015): 5 abilities
- 巨蝎勇士 (scorponok_bw_kabam): 5 abilities
- G1铁皮 (ironhide_gs_kabam): 4 abilities
- 猩猩队长 (optimusprimal_bw_mp32): 4 abilities
- 电影擎天柱 (optimusprime_cin_tf): 4 abilities (6 mods)
- 黑暗擎天柱 (nemesisprime_gs_voyager2015): 4 abilities
- 救护车 (ratchet_gs_kabam): 4 abilities
- 热破 (hotrod_cin_tlk): 4 abilities
- 飞毛腿 (sunstreaker_gs_deluxe2008): 3 abilities (4 mods)
- 补天士 (rodimusprime_gs_mp09): 3 abilities (4 mods)
- 碎骨魔 (bonecrusher_cin_rotf): 3 abilities
- 狂飙 (cyclonus_gs_uw06): 2 abilities (4 mods)
- 红蜘蛛 (fte_stars_gs_t3): 2 abilities (3 mods)
- 碾碎器 (grindor_cin_rotf): 1 ability
- 警车 (prowl_gs_deluxe2016): 1 ability (6 mods)
Total: 19 bots, 72 abilities.
"""

import unittest
import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "Server"))

import abilities
import gamedata


class TestAllPriorityAbilities(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        abilities.load_all_bots()
        cls.registered_bots = abilities.get_registered_bots()
        breakdown_file = ROOT / "tools" / "priority_72_breakdown.json"
        if breakdown_file.exists():
            with open(breakdown_file, "r", encoding="utf-8") as f:
                cls.breakdown_data = json.load(f)
        else:
            cls.breakdown_data = None

    def test_all_19_priority_bots_registered(self):
        expected_bots = [
            "grimlock_gs_mp08",
            "bumblebee_cin_dotm",
            "tantrum_gs_kabam",
            "thundercracker_gs_leader2015",
            "megatron_gs_leader2015",
            "scorponok_bw_kabam",
            "ironhide_gs_kabam",
            "optimusprimal_bw_mp32",
            "optimusprime_cin_tf",
            "nemesisprime_gs_voyager2015",
            "ratchet_gs_kabam",
            "hotrod_cin_tlk",
            "sunstreaker_gs_deluxe2008",
            "rodimusprime_gs_mp09",
            "bonecrusher_cin_rotf",
            "cyclonus_gs_uw06",
            "fte_stars_gs_t3",
            "grindor_cin_rotf",
            "prowl_gs_deluxe2016",
        ]
        self.assertEqual(len(expected_bots), 19)
        for bid in expected_bots:
            self.assertIn(bid, self.registered_bots, f"Bot {bid} must be registered!")

    def test_bot_mod_ids_coverage(self):
        expected_coverage = {
            "grimlock_gs_mp08": [
                "grimlock_takehit_melee_buff",
                "grimlock_dino_rage",
                "grimlock_heavy_burn",
                "grimlock_heavy_unstoppable",
                "grimlock_sp1_melee_buff",
                "grimlock_sp1_burn",
                "grimlock_sp2_melee_buff",
            ],
            "bumblebee_cin_dotm": [
                "bumblebee_cin_dotm_knockdown_atk",
                "bumblebee_cin_dotm_burst_atk",
                "bumblebee_cin_dotm_calib_melee",
                "bumblebee_cin_dotm_calib_ranged",
                "bumblebee_cin_dotm_sp1_armor_break",
                "bumblebee_cin_dotm_sp2_shock",
                "bumblebee_cin_dotm_sp3_shock",
            ],
            "tantrum_gs_kabam": [
                "tantrum_block_unstoppable",
                "tantrum_dash_melee_buff",
                "tantrum_innate_armor",
                "tantrum_sp3_unstoppable",
                "tantrum_sp3_melee_buff",
            ],
            "thundercracker_gs_leader2015": [
                "thundercracker_zero_crit",
                "thundercracker_heavy_purify",
                "thundercracker_purify_burn",
                "thundercracker_sp1_melee_buff",
                "thundercracker_sp3_shock",
            ],
            "megatron_gs_leader2015": [
                "megatron_fusion_cannon",
                "megatron_sp2_atk_debuff",
                "megatron_sp3_shock",
                "megatron_sp1_armor_break",
                "megatron_debuff_fusion",
            ],
            "scorponok_bw_kabam": [
                "scorponok_venom_charge",
                "scorponok_sp1_daze",
                "scorponok_venom_backfire_passive",
                "scorponok_venom_backfire_sp2",
                "scorponok_sp3_daze",
            ],
            "ironhide_gs_kabam": [
                "ironhide_sp1_melee_buff",
                "ironhide_sp2_unstoppable",
                "ironhide_sp2_armor_up",
                "ironhide_passive_armor_up",
            ],
            "optimusprimal_bw_mp32": [
                "optimusprimal_passive_armor_up",
                "optimusprimal_block_melee_buff",
                "optimusprimal_armor_to_melee",
                "optimusprimal_sp3_atk_debuff",
            ],
            "optimusprime_cin_tf": [
                "optimusprime_cin_tf_block_armor",
                "optimusprime_cin_tf_melee_buff",
                "optimusprime_cin_tf_willpower",
                "optimusprime_cin_tf_sp1_bleed",
                "optimusprime_cin_tf_sp1_dynamic_boost",
                "optimusprime_cin_tf_sp2_bleed",
            ],
            "nemesisprime_gs_voyager2015": [
                "nemesisprime_dark_energy",
                "nemesisprime_heavy_dispel",
                "nemesisprime_matrix_lifesteal",
                "nemesisprime_sp3_unblockable",
            ],
            "ratchet_gs_kabam": [
                "ratchet_self_diagnosis",
                "ratchet_sp1_wrench_stun",
                "ratchet_sp2_power_gain",
                "ratchet_sp2_repair",
            ],
            "hotrod_cin_tlk": [
                "hotrod_heavy_stun",
                "hotrod_decel_power_rate_debuff",
                "hotrod_sp2_deceleration",
                "hotrod_sp3_deceleration",
            ],
            "sunstreaker_gs_deluxe2008": [
                "sunstreaker_combo_power_gain",
                "sunstreaker_heavy_melee_buff",
                "sunstreaker_low_hp_unstoppable",
            ],
            "rodimusprime_gs_mp09": [
                "rodimus_dash_purify",
                "rodimus_melee_nullify_melee",
                "rodimus_melee_nullify_armor",
                "rodimus_heavy_armor_break",
            ],
            "bonecrusher_cin_rotf": [
                "bonecrusher_sp1_bleed",
                "bonecrusher_sp2_bleed",
                "bonecrusher_sp3_bleed",
            ],
            "cyclonus_gs_uw06": [
                "cyclonus_dark_burn_dmg",
                "cyclonus_dark_field_nullify",
                "cyclonus_unstoppable_counter_stun",
                "cyclonus_sp3_dark_field",
            ],
            "fte_stars_gs_t3": [
                "starscream_null_ray_dispel",
                "starscream_null_ray_shock_dmg",
                "starscream_evade_heavy_melee",
            ],
            "grindor_cin_rotf": [
                "grindor_struck_crit_debuff",
            ],
            "prowl_gs_deluxe2016": [
                "prowl_s1_power_burn",
                "prowl_s2_ranged_boost",
                "prowl_s3_power_lock",
                "prowl_melee_charge",
                "prowl_passive_melee_buff",
                "prowl_ranged_stun",
            ],
        }

        all_mods, all_appears, _ = abilities.collect_all_bot_statmods_and_appears()

        for bot_id, expected_mod_ids in expected_coverage.items():
            mod_ids = abilities.get_bot_mod_ids(bot_id)
            for m in expected_mod_ids:
                self.assertIn(m, mod_ids, f"Bot {bot_id} should have mod {m}")
                self.assertIn(m, all_mods, f"Mod {m} must be in all_mods")
                mod = all_mods[m]
                self.assertTrue(isinstance(mod.get("tr"), list), f"{m}.tr must be list")
                self.assertTrue(isinstance(mod.get("uit"), list), f"{m}.uit must be list")
                self.assertTrue(isinstance(mod.get("a"), list), f"{m}.a must be list")

                # Verify appearance colors (pure 6 hex digits)
                for aid in mod.get("a", []):
                    if aid in all_appears:
                        appr = all_appears[aid]
                        for ckey in ("tc", "gt", "gb", "bc"):
                            if ckey in appr and appr[ckey]:
                                c = appr[ckey]
                                self.assertFalse(c.startswith("#"), f"Color {ckey} in {aid} cannot have '#': {c}")
                                self.assertEqual(len(c), 6, f"Color {ckey} in {aid} must be 6 hex: {c}")

    def test_gamedata_hero_entries_for_all_19_bots(self):
        for bid in [
            "grimlock_gs_mp08", "bumblebee_cin_dotm", "tantrum_gs_kabam",
            "thundercracker_gs_leader2015", "megatron_gs_leader2015", "scorponok_bw_kabam",
            "ironhide_gs_kabam", "optimusprimal_bw_mp32", "optimusprime_cin_tf",
            "nemesisprime_gs_voyager2015", "ratchet_gs_kabam", "hotrod_cin_tlk",
            "sunstreaker_gs_deluxe2008", "rodimusprime_gs_mp09", "bonecrusher_cin_rotf",
            "cyclonus_gs_uw06", "fte_stars_gs_t3", "grindor_cin_rotf", "prowl_gs_deluxe2016"
        ]:
            hero_entry = gamedata.build_hero_entry(bid, 5, 50)
            self.assertIn("stat_mods", hero_entry, f"Hero {bid} entry missing stat_mods")
            self.assertTrue(len(hero_entry["stat_mods"]) > 0, f"Hero {bid} must have stat_mods")


if __name__ == "__main__":
    unittest.main()
