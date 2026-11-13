#!/usr/bin/env python3
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from Server.abilities.bots.dirge import build_dirge_abilities, BOT_ID


class TestDirgeAbility(unittest.TestCase):
    def test_dirge_ability_contracts(self):
        """验证挽歌所有能力契约与数值结构"""
        base_hp = 44950.0
        base_atk = 2945.0
        mods, appears, buffs = build_dirge_abilities(base_hp=base_hp, base_atk=base_atk)

        # 1. 恐惧常驻状态
        self.assertIn("dirge_fear_debuff", mods)
        self.assertIn("appr_dirge_fear", appears)
        fear_mod = mods["dirge_fear_debuff"]
        self.assertEqual(fear_mod["d"], -1.0)
        self.assertEqual(fear_mod["ta"], "opponent")
        self.assertEqual(fear_mod["mt"], "debuff")
        self.assertEqual(fear_mod["tr"], [])
        self.assertEqual(fear_mod["st"], 1)

        # 2. 恐惧阴影
        self.assertIn("dirge_fear_shadow", mods)
        self.assertIn("appr_dirge_fear_shadow", appears)
        shadow_mod = mods["dirge_fear_shadow"]
        self.assertEqual(shadow_mod["st"], 3)
        self.assertEqual(shadow_mod["ta"], "opponent")

        # 3. 冷酷嘲讽
        self.assertIn("dirge_sig_mockery", mods)
        self.assertIn("appr_dirge_sig_mockery", appears)
        mockery_mod = mods["dirge_sig_mockery"]
        self.assertEqual(mockery_mod["d"], 5.0)
        self.assertEqual(mockery_mod["m"], 0.60)
        self.assertEqual(mockery_mod["tr"], ["onEvade"])

        # 4. 恐惧流血预备 (10s) 与 伤害结算 (2s, 145% ATK)
        self.assertIn("dirge_bleed_timer", mods)
        self.assertIn("dirge_fear_bleed", mods)
        bleed_mod = mods["dirge_fear_bleed"]
        expected_bleed_dmg = float(round(base_atk * 1.45))
        self.assertEqual(bleed_mod["m"], expected_bleed_dmg)
        self.assertEqual(bleed_mod["d"], 2.0)
        self.assertEqual(bleed_mod["tr"], [])  # 严禁配置 onHit，完全由 10s 倒计时触发

        # 5. 暴击几率 (+40% crit rate)
        self.assertIn("dirge_fear_crit_buff", mods)
        crit_mod = mods["dirge_fear_crit_buff"]
        self.assertEqual(crit_mod["m"], 0.40)

        # 6. 敌方闪避减益 (-40% ATK, 5s)
        self.assertIn("dirge_evade_atk_debuff", mods)
        debuff_mod = mods["dirge_evade_atk_debuff"]
        self.assertEqual(debuff_mod["m"], -0.40)
        self.assertEqual(debuff_mod["d"], 5.0)
        self.assertEqual(debuff_mod["ta"], "opponent")

        # 7. 暴击伤害 (+30% crit dmg)
        self.assertIn("dirge_bleed_crit_dmg", mods)
        cdmg_mod = mods["dirge_bleed_crit_dmg"]
        self.assertEqual(cdmg_mod["m"], 0.30)

        # 8. 能量功率 (+10% power rate)
        self.assertIn("dirge_bleed_power_rate", mods)
        power_mod = mods["dirge_bleed_power_rate"]
        self.assertEqual(power_mod["m"], 0.10)
        # 验证紫色图标使用 core.py 标准浅紫色 (LIGHT_PURPLE_POWER: C4BBF8 / 7E22CE)
        self.assertEqual(appears["appr_dirge_bleed_power_rate"]["tc"], "C4BBF8")
        self.assertEqual(appears["appr_dirge_bleed_power_rate"]["gb"], "7E22CE")

        # 9. SP1 特殊伤害 (+35% ATK)
        self.assertIn("dirge_sp1_fear_boost", mods)
        sp1_mod = mods["dirge_sp1_fear_boost"]
        self.assertEqual(sp1_mod["m"], 0.35)

        # 10. SP2 燃烧 (35% ATK 4s & 恐惧强化 70% ATK 8s)
        self.assertIn("dirge_sp2_burn", mods)
        self.assertIn("dirge_sp2_burn_fear", mods)
        sp2_norm = mods["dirge_sp2_burn"]
        sp2_fear = mods["dirge_sp2_burn_fear"]
        self.assertEqual(sp2_norm["m"], float(round(base_atk * 0.35)))
        self.assertEqual(sp2_norm["d"], 4.0)
        self.assertEqual(sp2_norm["tr"], [])
        self.assertEqual(sp2_fear["m"], float(round(base_atk * 0.70)))
        self.assertEqual(sp2_fear["d"], 8.0)
        self.assertEqual(sp2_fear["tr"], [])

        # 11. SP3 强化恐惧 (30s)
        self.assertIn("dirge_sp3_fear_empower", mods)
        sp3_mod = mods["dirge_sp3_fear_empower"]
        self.assertEqual(sp3_mod["d"], 30.0)

        # 12. 专属底层 BuffEffect 模板 (流血倒计时灰色圆环、恐惧、阴影)
        self.assertIn("dirge_bleed_timer", buffs)
        self.assertEqual(buffs["dirge_bleed_timer"]["time"]["amount"], 10.0)
        self.assertEqual(appears["appr_dirge_bleed_timer"]["tc"], "CBD5E1")
        self.assertEqual(appears["appr_dirge_bleed_timer"]["gb"], "94A3B8")
        self.assertIn("dirge_fear", buffs)
        self.assertIn("dirge_shadow", buffs)


if __name__ == "__main__":
    unittest.main()
