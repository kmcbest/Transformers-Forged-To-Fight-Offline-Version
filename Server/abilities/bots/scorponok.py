#!/usr/bin/env python3
"""
Bot Ability Implementation: 巨蝎勇士 (Scorponok BW)
===================================================
Bot ID: scorponok_bw_kabam
阵营: 原始兽 (Predacon) | 职业: 勇士系 (Warrior)

【官方技能真理源对照 (来自 Upstash KV 聚合 Priorities 清单)】：
-----------------------------------------------------------------------------
1. [被动 - 近战流血 / Melee Crit Bleed] (ID: 3275, pua_icon: 0xe401, category: passive)
   - 官方描述: "近战攻击出暴击时，40%的概率触发流血，施加攻击力60%的伤害，持续4秒"
   - 实现方案:
     scorponok_melee_crit_bleed:
       触发 onCrit, level=Light,Medium,Heavy, 40% 概率施加 4.0 秒流血 debuff (60% base_atk 伤害),
       作用于 opponent, 红色血条圆环图标 (PUA: 0xe401, Hex: FF0000 / B91C1C),
       呼出文字: "BLEED"。
-----------------------------------------------------------------------------
"""

from ..core import make_bleed_statmod
from ..registry import register_bot

BOT_ID = "scorponok_bw_kabam"


@register_bot(BOT_ID, name_zh="巨蝎勇士", desc="勇士系近战凶兽，近战暴击毒刺流血")
def build_scorponok_abilities(base_hp: float = 34867.0, base_atk: float = 2321.0):
    mods = {}
    appears = {}
    buffs = {}

    # 1. 近战暴击流血 (60% ATK: 2321 * 0.6 = 1393, 持续 4 秒, 40% 几率)
    m1, a1 = make_bleed_statmod(
        mod_id="scorponok_melee_crit_bleed",
        duration=4.0,
        total_dmg=float(round(base_atk * 0.60)),
        chance=0.40,
        trigger="onCrit",
        trigger_scope="level=Light,Medium,Heavy",
        appr_id="appr_scorponok_bleed",
        callout_text="BLEED",
        buff_id="dmg_bleed",
    )
    mods.update(m1)
    appears.update(a1)

    return mods, appears, buffs
