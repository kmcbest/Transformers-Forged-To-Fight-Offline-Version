#!/usr/bin/env python3
"""
Bot Ability Implementation: 电影铁皮 (Ironhide ROTF)
===================================================
Bot ID: ironhide_cin_rotf
阵营: 汽车人 (Autobot) | 职业: 破坏系 (Demolition)

【官方技能真理源对照 (来自 Upstash KV 聚合 Priorities 清单)】：
-----------------------------------------------------------------------------
1. [被动 - 燃烧 / Missile Burn] (ID: 2589, pua_icon: 0xe41d, category: passive)
   - 官方描述: "所有导弹攻击（重击、SP1的最后一击，SP2的所有攻击）命中时有70%几率造成燃烧，施加攻击力80%的伤害，持续4秒。 如果对手正在燃烧中，则燃烧可以叠加，每层依旧是4秒，但伤害为攻击力的30%。"
   - 实现方案:
     ironhide_missile_burn: 触发 onHit, level=Heavy,Special1,Special2, 70% 概率施加 4.0 秒燃烧 (80% ATK 伤害), 呼出 "燃烧"。
     ironhide_missile_burn_stack: 触发 onHit, level=Heavy,Special1,Special2;opp.status=dmg_burn, 70% 概率叠加 4.0 秒燃烧 (30% ATK 伤害)。

2. [被动 - 导弹暴击 / Missile Crit] (ID: 2605, pua_icon: 0xe40d, category: passive)
   - 官方描述: "所有导弹攻击（重击、SP1的最后一击，SP2的所有攻击）+100%暴击概率"
   - 实现方案:
     ironhide_missile_crit: 触发 onAttackStarted, level=Heavy,Special1,Special2, 100% 暴击率加成 (持续 0.8 秒覆盖单次攻击)。

3. [SP2 - 暴击伤害 / Critical Damage Boost] (ID: 2596, pua_icon: 0xe406, category: sp2)
   - 官方描述: "有76%的概率获得暴击伤害增益，增加75%的暴击伤害，持续4秒"
   - 实现方案:
     ironhide_s2_crit_dmg: 触发 onSpecial2Activate, 76% 概率获得 4.0 秒暴击伤害增益 (+75% 暴击伤害)。

4. [SP3 - 燃烧 / Heavy Artillery Burn] (ID: 2606, pua_icon: 0xe41d, category: sp3)
   - 官方描述: "最后一击有30%几率造成燃烧，施加攻击力100%的伤害，持续8秒。"
   - 实现方案:
     ironhide_s3_burn: 触发 onHit, level=Special3, 30% 概率施加 8.0 秒燃烧 (100% ATK 伤害)。
-----------------------------------------------------------------------------
"""

from ..core import make_burn_statmod, make_crit_rate_statmod, make_crit_damage_statmod
from ..registry import register_bot

BOT_ID = "ironhide_cin_rotf"


@register_bot(BOT_ID, name_zh="电影铁皮", desc="破坏系重炮手，重击/SP导弹暴击与叠层燃烧、SP2暴击伤害增益")
def build_ironhide_abilities(base_hp: float = 33602.0, base_atk: float = 2531.0):
    mods = {}
    appears = {}
    buffs = {}

    # 1. 导弹初次燃烧 (80% ATK: 2531 * 0.8 = 2025, 持续 4 秒)
    m1, a1 = make_burn_statmod(
        mod_id="ironhide_missile_burn",
        duration=4.0,
        total_dmg=float(round(base_atk * 0.80)),
        chance=0.70,
        trigger="onHit",
        trigger_scope="level=Heavy,Special1,Special2",
        callout_text="燃烧",
        stackable=True,
        pua_icon="\uE41D",
    )
    mods.update(m1)
    appears.update(a1)

    # 1.2 导弹叠层燃烧 (30% ATK: 2531 * 0.3 = 759, 持续 4 秒, 对手在燃烧中触发)
    m1_stack, a1_stack = make_burn_statmod(
        mod_id="ironhide_missile_burn_stack",
        duration=4.0,
        total_dmg=float(round(base_atk * 0.30)),
        chance=0.70,
        trigger="onHit",
        trigger_scope="level=Heavy,Special1,Special2;opp.status=dmg_burn",
        callout_text="燃烧",
        stackable=True,
        pua_icon="\uE41D",
    )
    mods.update(m1_stack)
    appears.update(a1_stack)

    # 2. 导弹攻击 +100% 暴击几率
    m2, a2 = make_crit_rate_statmod(
        mod_id="ironhide_missile_crit",
        duration=0.8,
        crit_bonus=1.00,
        chance=1.0,
        trigger="onAttackStarted",
        trigger_scope="level=Heavy,Special1,Special2",
        callout_text="导弹暴击",
        pua_icon="\uE40D",
    )
    mods.update(m2)
    appears.update(a2)

    # 3. SP2 暴击伤害增益 (+75% 暴击伤害, 持续 4 秒, 76% 几率)
    m3, a3 = make_crit_damage_statmod(
        mod_id="ironhide_s2_crit_dmg",
        duration=4.0,
        crit_dmg_bonus=0.75,
        chance=0.76,
        trigger="onSpecial2Activate",
        callout_text="暴击伤害",
        pua_icon="\uE406",
    )
    mods.update(m3)
    appears.update(a3)

    # 4. SP3 燃烧 (100% ATK: 2531 持续 8 秒, 30% 几率)
    m4, a4 = make_burn_statmod(
        mod_id="ironhide_s3_burn",
        duration=8.0,
        total_dmg=float(round(base_atk * 1.00)),
        chance=0.30,
        trigger="onHit",
        trigger_scope="level=Special3",
        callout_text="燃烧",
        stackable=True,
        pua_icon="\uE41D",
    )
    mods.update(m4)
    appears.update(a4)

    return mods, appears, buffs
