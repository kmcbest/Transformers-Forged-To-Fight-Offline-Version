#!/usr/bin/env python3
"""
Bot Ability Implementation: 狂飙 (Cyclonus UW-06)
================================================
Bot ID: cyclonus_gs_uw06
职业: 战术系 (Tactician)

【官方技能真理源对照 (来自 Upstash KV 聚合 72 Priorities 清单)】：
-----------------------------------------------------------------------------
1. [被动 - 黑暗场 / Dark Field] (ID: 2973, category: passive)
   - 官方描述: "当狂飙获得一层黑暗能量或在拥有黑暗能量的情况下使用L4或者M2命中对手时，他会放出黑暗场脉冲。
     黑暗场对对方造成黑暗燃烧，立即造成攻击力20%的伤害，并有70%的概率驱散对方一个增益。如果对方处于不可阻挡的状态，概率变为100%
     如果具有不可阻挡增益的对手冲向狂飙，他会立即获得黑暗能量，驱散不可阻挡增益，并造成1.5秒眩晕。"
2. [SP3 - 黑暗场 / Dark Field] (ID: 2991, category: sp3)
   - 官方描述: "狂飙获得黑暗能量，并且在10秒内连续释放黑暗场脉冲。"
-----------------------------------------------------------------------------
"""

from ..core import (
    make_direct_dmg_statmod,
    make_nullify_statmod,
    make_stun_statmod,
    validate_statmod,
    validate_appear,
)
from ..registry import register_bot

BOT_ID = "cyclonus_gs_uw06"


@register_bot(BOT_ID, name_zh="狂飙", desc="战术系，黑暗场脉冲、黑暗燃烧与霸体克星反制眩晕")
def build_cyclonus_abilities(base_hp: float = 32000.0, base_atk: float = 2950.0):
    mods = {}
    appears = {}
    buffs = {}

    # 1. ID 2973: 黑暗场脉冲 - 黑暗燃烧 20% ATK 即时伤害 (L4/M2 onHit)
    dark_burn_dmg = float(round(base_atk * 0.20, 2))
    appr_dark_burn = {
        "id": "appr_cyclonus_dark_burn",
        "a": "黑暗燃烧",
        "s": "",
        "l": "黑暗能量侵蚀",
        "ss": "黑暗燃烧",
        "t": "\uE41D",
        "f": "",
        "st": "黑暗燃烧",
        "ps": "黑暗燃烧",
        "pl": "黑暗燃烧中",
        "tc": "8800FF",
        "gt": "8800FF",
        "gb": "440088",
    }
    m_dmg, _ = make_direct_dmg_statmod(
        mod_id="cyclonus_dark_burn_dmg",
        dmg=dark_burn_dmg,
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Light,Medium",
    )
    mods.update(m_dmg)
    appears["appr_cyclonus_dark_burn"] = appr_dark_burn

    # 黑暗场驱散: 70% 几率驱散一个增益 (对霸体 100% 驱散)
    m_null, a_null = make_nullify_statmod(
        mod_id="cyclonus_dark_field_nullify",
        chance=0.70,
        trigger="onHit",
        trigger_scope="level=Light,Medium",
        appr_id="appr_cyclonus_nullify",
        callout_text="驱散",
        target_categories=None,
    )
    mods.update(m_null)
    appears.update(a_null)

    # 霸体冲向狂飙反制: 1.5s 眩晕
    m_stun, a_stun = make_stun_statmod(
        mod_id="cyclonus_unstoppable_counter_stun",
        duration=1.5,
        chance=1.0,
        trigger="onDash",
        trigger_scope="",
        appr_id="appr_cyclonus_stun",
        callout_text="眩晕",
        target_actor="opponent",
    )
    mods.update(m_stun)
    appears.update(a_stun)

    # 2. ID 2991: SP3 释放 10 秒持续黑暗场脉冲
    statmod_sp3 = {
        "id": "cyclonus_sp3_dark_field",
        "t": "buff",
        "tm": "",
        "tr": ["onSpecial3Activate"],
        "uit": ["onSpecial3Activate"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 1.0,
        "d": 10.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_cyclonus_dark_burn"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(statmod_sp3)
    mods["cyclonus_sp3_dark_field"] = statmod_sp3

    return mods, appears, buffs
