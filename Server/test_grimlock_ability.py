import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from Server.abilities.bots.grimlock import build_grimlock_abilities, BOT_ID


class TestGrimlockAbility(unittest.TestCase):
    def test_grimlock_sp1_burn_contract(self):
        """验证钢锁 SP1 燃烧能力契约：必须仅在终结击（第2击喷火）命中时触发"""
        mods, appears = build_grimlock_abilities()

        # 检查 ID 存在
        self.assertIn("grimlock_sp1_burn", mods)
        self.assertIn("appr_grimlock_sp1_burn", appears)

        mod = mods["grimlock_sp1_burn"]
        appr = appears["appr_grimlock_sp1_burn"]

        # 核心触发契约：必须是 onHit 且 trigger_scope 包含 level=Special1 与 dmgFlags=LastHit
        self.assertEqual(mod["tr"], ["onHit"])
        self.assertEqual(mod["trs"], "level=Special1;dmgFlags=LastHit")
        self.assertEqual(mod["c"], 1.0)
        self.assertEqual(mod["d"], 4.0)

        # 检查外观
        self.assertEqual(appr["a"], "燃烧")
        self.assertEqual(appr["t"], "\uE41D")


if __name__ == "__main__":
    unittest.main()
