#!/usr/bin/env python3
"""
Unit test for Wheeljack, Rhinox, Ratchet, and Arcee ability configurations.
Verifies SP hit triggers, final hit scopes (dmgFlags=LastHit), callouts, and colors.
"""
import io
import os
import sys
import unittest

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import abilities
import gamedata


class TestBatchAbilities(unittest.TestCase):
    def test_wheeljack_final_hit_and_triggers(self):
        """Wheeljack SP1, SP2, SP3 debuffs must only trigger on onSpecialXHit with dmgFlags=LastHit."""
        mods = gamedata.build_stat_modifiers()
        appears = gamedata.build_stat_mod_appears()

        for sp_key, sp_trigger in [
            ("sp1", "onSpecial1Hit"),
            ("sp2", "onSpecial2Hit"),
            ("sp3", "onSpecial3Hit"),
        ]:
            shock_id = f"wheeljack_{sp_key}_shock"
            leak_id = f"wheeljack_{sp_key}_leak"
            stun_id = f"wheeljack_{sp_key}_stun"

            for mod_id in [shock_id, leak_id, stun_id]:
                self.assertIn(mod_id, mods, f"Missing {mod_id}")
                m = mods[mod_id]
                self.assertEqual(m["tr"], [sp_trigger], f"{mod_id} trigger must be {sp_trigger}")
                self.assertEqual(m["trs"], "dmgFlags=LastHit", f"{mod_id} must have scope dmgFlags=LastHit")
                self.assertEqual(m["ta"], "opponent")
                self.assertEqual(m["mt"], "debuff")

            # Check shock
            shock = mods[shock_id]
            self.assertEqual(shock["c"], 0.60)
            self.assertEqual(shock["d"], 6.0)

            # Check leak
            leak = mods[leak_id]
            expected_chance = 1.0 if sp_key in ("sp2", "sp3") else 0.50
            self.assertEqual(leak["c"], expected_chance)
            self.assertEqual(leak["d"], 3.0)
            self.assertEqual(leak["t"], "power_gain")
            self.assertLess(leak["m"], 0.0)

            # Check stun
            stun = mods[stun_id]
            self.assertEqual(stun["c"], 0.10)
            self.assertEqual(stun["d"], 3.0)

            # Check colors: Shock & Leak must be pure FF0000 (red)
            appr_shock = appears[f"appr_{shock_id}"]
            self.assertEqual(appr_shock["tc"], "FF0000")
            self.assertEqual(appr_shock["st"], "震击")

            appr_leak = appears[f"appr_{leak_id}"]
            self.assertEqual(appr_leak["tc"], "FF0000")
            self.assertEqual(appr_leak["st"], "能量流失")

            appr_stun = appears[f"appr_{stun_id}"]
            self.assertEqual(appr_stun["st"], "眩晕")

    def test_rhinox_sp_triggers(self):
        """Rhinox SP1 nullify & bleed must trigger on onSpecial1Hit, SP2 on onSpecial2Hit."""
        mods = gamedata.build_stat_modifiers()
        appears = gamedata.build_stat_mod_appears()

        # SP1 Nullify
        null_mod = mods["rhinox_sp1_nullify"]
        self.assertEqual(null_mod["tr"], ["onSpecial1Hit"])
        self.assertEqual(null_mod["ta"], "opponent")

        # SP1 Nullify Bleed
        nb_mod = mods["rhinox_sp1_nullify_bleed"]
        self.assertEqual(nb_mod["tr"], ["onSpecial1Hit"])
        self.assertEqual(nb_mod["d"], 14.0)
        self.assertEqual(nb_mod["ta"], "opponent")
        appr_nb = appears["appr_rhinox_nullify_bleed"]
        self.assertEqual(appr_nb["tc"], "FF0000")
        self.assertEqual(appr_nb["st"], "流血")

        # SP2 Bleed
        sp2_mod = mods["rhinox_sp2_bleed"]
        self.assertEqual(sp2_mod["tr"], ["onSpecial2Hit"])
        self.assertEqual(sp2_mod["d"], 8.0)
        self.assertEqual(sp2_mod["c"], 0.40)

        # Passive Ranged Bleed
        rb_mod = mods["rhinox_ranged_bleed"]
        self.assertEqual(rb_mod["tr"], ["onHit"])
        self.assertEqual(rb_mod["trs"], "level=Ranged")
        self.assertEqual(rb_mod["c"], 0.30)
        self.assertEqual(rb_mod["d"], 5.0)

    def test_arcee_sp_triggers(self):
        """Arcee SP1 Trick Shot must trigger on onSpecial1Hit."""
        mods = gamedata.build_stat_modifiers()
        appears = gamedata.build_stat_mod_appears()

        sp1_mod = mods["arcee_sp1_trick_shot"]
        self.assertEqual(sp1_mod["tr"], ["onSpecial1Hit"])
        self.assertEqual(sp1_mod["ta"], "self")
        self.assertEqual(sp1_mod["mt"], "buff")
        self.assertEqual(sp1_mod["m"], 0.35)
        self.assertEqual(sp1_mod["d"], 6.5)

        appr_sp1 = appears["appr_arcee_sp1_boost"]
        self.assertEqual(appr_sp1["tc"], "FFAA00")
        self.assertEqual(appr_sp1["st"], "特技射击")

    def test_ratchet_sp_triggers(self):
        """Ratchet SP3 Diagnostic Scan must trigger on onSpecial3Hit."""
        mods = gamedata.build_stat_modifiers()
        sp3_mod = mods["ratchet_sp3_shock"]
        self.assertEqual(sp3_mod["tr"], ["onSpecial3Hit"])
        self.assertEqual(sp3_mod["d"], 4.0)
        self.assertEqual(sp3_mod["ta"], "opponent")


if __name__ == "__main__":
    unittest.main()
