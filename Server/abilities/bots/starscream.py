#!/usr/bin/env python3
"""
Bot Ability Implementation: 红蜘蛛 (Starscream G1)
=================================================
Bot ID: fte_stars_gs_t3
阵营: 霸天虎 (Decepticon) | 职业: 战术系 (Tactician)

【官方技能真理源对照 (来自 Upstash KV 聚合 Priorities 清单)】：
-----------------------------------------------------------------------------
1. [被动 - 燃烧 / Heavy Burn] (ID: 2378, pua_icon: 0xe41d, category: passive)
   - 官方描述: "重击命中时有20%几率造成燃烧，施加攻击力40%的伤害，持续4秒。"
   - 实现方案:
     starscream_heavy_burn:
       触发 onHit, level=Heavy, 20% 概率施加 4.0 秒燃烧 debuff (40% base_atk 伤害),
       作用于 opponent, 橙红血条圆环图标 (PUA: 0xe41d, Hex: FF6600 / CC3300),
       呼出文字: "燃烧"。
-----------------------------------------------------------------------------
"""

from ..core import make_burn_statmod
from ..registry import register_bot

BOT_ID = "fte_stars_gs_t3"


@register_bot(BOT_ID, name_zh="红蜘蛛", desc="战术系空中指挥官，重击火焰燃烧")
def build_starscream_abilities(base_hp: float = 34626.0, base_atk: float = 2859.0):
    mods = {}
    appears = {}
    buffs = {}

    # 1. 重击燃烧 (40% ATK: 2859 * 0.4 = 1144, 20% 几率, 持续 4 秒)
    m1, a1 = make_burn_statmod(
        mod_id="starscream_heavy_burn",
        duration=4.0,
        total_dmg=float(round(base_atk * 0.40)),
        chance=0.20,
        trigger="onHit",
        trigger_scope="level=Heavy",
        callout_text="燃烧",
        stackable=True,
        pua_icon="\uE41D",
    )
    mods.update(m1)
    appears.update(a1)

    return mods, appears, buffs
