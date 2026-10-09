#!/usr/bin/env python3
"""
Bot Ability Implementation: 黄蜂勇士 (Waspinator)
===============================================
Bot ID: waspinator_gs_deluxe
阵营: 原始兽 (Predacon) | 职业: 破坏系 (Demolition)

【官方技能真理源对照 (来自 Upstash KV 聚合 Priorities 清单)】：
-----------------------------------------------------------------------------
1. [SP3 - 燃烧 / Stinger Blast Burn] (ID: 3470, pua_icon: 0xe41d, category: sp3)
   - 官方描述: "100%概率施加燃烧，造成攻击力100%的伤害，持续5秒。"
   - 实现方案:
     waspinator_s3_burn: 触发 onHit, level=Special3, 100% 概率施加 5.0 秒燃烧 (100% base_atk 伤害)。
-----------------------------------------------------------------------------
"""

from ..core import make_burn_statmod
from ..registry import register_bot

BOT_ID = "waspinator_gs_deluxe"


@register_bot(BOT_ID, name_zh="黄蜂勇士", desc="破坏系空战毒刺，SP3毒刺重炮致命燃烧")
def build_waspinator_abilities(base_hp: float = 29598.0, base_atk: float = 2191.0):
    mods = {}
    appears = {}
    buffs = {}

    # 1. SP3 燃烧 (100% ATK: 2191 * 1.0 = 2191, 持续 5 秒, 100% 几率)
    m1, a1 = make_burn_statmod(
        mod_id="waspinator_s3_burn",
        duration=5.0,
        total_dmg=float(round(base_atk * 1.00)),
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Special3",
        callout_text="燃烧",
        stackable=True,
        pua_icon="\uE41D",
    )
    mods.update(m1)
    appears.update(a1)

    return mods, appears, buffs
