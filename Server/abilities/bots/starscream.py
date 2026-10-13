#!/usr/bin/env python3
"""
Bot Ability Implementation: 红蜘蛛 (Starscream G1)
=================================================
Bot ID: fte_stars_gs_t3
职业: 战术系 (Tactician)

【官方技能真理源对照 (来自 Upstash KV 聚合 72 Priorities 清单)】：
-----------------------------------------------------------------------------
1. [被动 - 零射线 / Null Ray] (ID: 2357, category: passive)
   - 官方描述: "基础远程攻击命中时100%概率驱散一个护甲、近战或者攻击增益。驱散时造成攻击力90%的即时震击伤害。"
2. [被动 - 规避近战重击 / Evade Heavy Melee] (ID: 2362, category: passive)
   - 官方描述: "20%的概率机规避近战重击。//无图标，天然技能，在敌人近战重击即将命中时计算概率"
-----------------------------------------------------------------------------
"""

from ..core import (
    make_burn_statmod,
    make_direct_dmg_statmod,
    make_nullify_statmod,
    make_evade_statmod,
)
from ..registry import register_bot

BOT_ID = "fte_stars_gs_t3"


@register_bot(BOT_ID, name_zh="红蜘蛛", desc="战术系空中指挥官，零射线驱散震击与重击规避")
def build_starscream_abilities(base_hp: float = 34626.0, base_atk: float = 2859.0):
    mods = {}
    appears = {}
    buffs = {}

    # 1. ID 2357: 基础远程攻击 100% 驱散 1 个增益
    m_null, a_null = make_nullify_statmod(
        mod_id="starscream_null_ray_dispel",
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Ranged",
        appr_id="appr_starscream_null_ray",
        callout_text="驱散",
        target_categories=None,
    )
    mods.update(m_null)
    appears.update(a_null)

    # 驱散时造成 90% ATK 即时震击伤害
    shock_dmg = float(round(base_atk * 0.90, 2))
    m_shock, _ = make_direct_dmg_statmod(
        mod_id="starscream_null_ray_shock_dmg",
        dmg=shock_dmg,
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Ranged",
        buff_id="dmg_shock",
    )
    mods.update(m_shock)

    # 2. ID 2362: 20% 概率规避近战重击
    m_evade, a_evade = make_evade_statmod(
        mod_id="starscream_evade_heavy_melee",
        evade_type="melee",
        duration=0.5,
        chance=0.20,
        trigger="onIncomingHit",
        trigger_scope="level=Heavy",
        appr_id="appr_starscream_evade",
        callout_text="规避",
    )
    mods.update(m_evade)
    appears.update(a_evade)

# 3. [既有技能保留] 重击燃烧 (ID: 2378): 20% 几率造成 4.0 秒燃烧 (40% ATK)
    m_burn, a_burn = make_burn_statmod(
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
    mods.update(m_burn)
    appears.update(a_burn)

    return mods, appears, buffs

