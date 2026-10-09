#!/usr/bin/env python3
"""
Bot Ability Implementation: 搅拌者 (Mixmaster ROTF)
===================================================
Bot ID: mixmaster_cin_rotf
阵营: 霸天虎 (Decepticon) | 职业: 破坏系 (Demolition)

【官方技能真理源对照 (来自 Upstash KV 聚合 Priorities 清单)】：
-----------------------------------------------------------------------------
1. [SP2 - 强酸/腐蚀燃烧 / Acid Burn] (ID: 3178, pua_icon: 0xe41d, category: sp2)
   - 官方描述: "60%概率造成燃烧，施加攻击力100%的伤害，持续8秒。"
   - 实现方案:
     mixmaster_s2_burn: 触发 onHit, level=Special2, 60% 概率施加 8.0 秒燃烧 (100% ATK 伤害)。

2. [SP3 - 熔炉烈焰 / Caustic Blast Burn] (ID: 3179, pua_icon: 0xe41d, category: sp3)
   - 官方描述: "70%概率造成燃烧，施加攻击力120%的伤害，持续8秒。"
   - 实现方案:
     mixmaster_s3_burn: 触发 onHit, level=Special3, 70% 概率施加 8.0 秒燃烧 (120% ATK 伤害)。
-----------------------------------------------------------------------------
"""

from ..core import make_burn_statmod
from ..registry import register_bot

BOT_ID = "mixmaster_cin_rotf"


@register_bot(BOT_ID, name_zh="搅拌者", desc="破坏系重型化学炮手，SP2强酸燃烧、SP3重熔炮高伤烈焰")
def build_mixmaster_abilities(base_hp: float = 32402.0, base_atk: float = 2306.0):
    mods = {}
    appears = {}
    buffs = {}

    # 1. SP2 燃烧 (100% ATK: 2306 * 1.0 = 2306, 持续 8 秒, 60% 几率)
    m1, a1 = make_burn_statmod(
        mod_id="mixmaster_s2_burn",
        duration=8.0,
        total_dmg=float(round(base_atk * 1.00)),
        chance=0.60,
        trigger="onHit",
        trigger_scope="level=Special2;index=1,2",
        callout_text="燃烧",
        stackable=True,
        pua_icon="\uE41D",
    )
    mods.update(m1)
    appears.update(a1)

    # 2. SP3 燃烧 (120% ATK: 2306 * 1.2 = 2767, 持续 8 秒, 70% 几率)
    m2, a2 = make_burn_statmod(
        mod_id="mixmaster_s3_burn",
        duration=8.0,
        total_dmg=float(round(base_atk * 1.20)),
        chance=0.70,
        trigger="onHit",
        trigger_scope="level=Special3",
        callout_text="燃烧",
        stackable=True,
        pua_icon="\uE41D",
    )
    mods.update(m2)
    appears.update(a2)

    return mods, appears, buffs
