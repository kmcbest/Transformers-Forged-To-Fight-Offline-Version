#!/usr/bin/env python3
"""
Bot Ability Implementation: 补天士 (Rodimus Prime MP-09)
========================================================
Bot ID: rodimusprime_gs_mp09
职业: 战术系 (Tactician)

【官方技能真理源对照 (来自 Upstash KV 聚合 72 Priorities 清单)】：
-----------------------------------------------------------------------------
1. [被动 - 前冲净化 / Dashing Purify] (ID: 2796, category: passive)
   - 官方描述: "前冲时有70%的概率净化补天士身上的一个减益。//无图标，净化成功显示文字“净化！”"
2. [被动 - 近战驱散 / Melee Nullify] (ID: 2798, category: passive)
   - 官方描述: "近战组合的最后一击（M2或者L2）命中时：50%概率驱散对方一个近战增益，50%概率驱散对方一个护甲增益"
3. [被动 - 重击破甲 / Heavy Attack Armor Break] (ID: 2801, category: passive)
   - 官方描述: "重击命中时，对方身上有几个增益，就施加几层破甲，每层强度15%，持续7秒。同时移除对方身上所有的护甲增益。"
-----------------------------------------------------------------------------
"""

from ..core import (
    make_armor_break_statmod,
    make_nullify_statmod,
    validate_statmod,
    validate_appear,
)
from ..registry import register_bot

BOT_ID = "rodimusprime_gs_mp09"


@register_bot(BOT_ID, name_zh="补天士", desc="战术系领袖，前冲净化、连招驱散与重击按增益层数叠破甲")
def build_rodimusprime_abilities(base_hp: float = 33000.0, base_atk: float = 3100.0):
    mods = {}
    appears = {}
    buffs = {}

    # 1. ID 2796: 前冲 70% 概率净化自身一个减益 (呼出大字: 净化！)
    appr_purify = {
        "id": "appr_rodimus_purify",
        "a": "净化！",
        "s": "",
        "l": "净化负面状态",
        "ss": "净化",
        "t": "",
        "f": "",
        "st": "净化！",
        "ps": "净化",
        "pl": "净化生效",
        "tc": "00FF66",
        "gt": "00FF66",
        "gb": "009933",
    }
    statmod_purify = {
        "id": "rodimus_dash_purify",
        "t": "remove",
        "tm": "",
        "tr": ["onDash"],
        "uit": ["onDash"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 0.70,
        "m": 1.0,
        "d": 0.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 0,
        "g": "",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_rodimus_purify"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(statmod_purify)
    validate_appear(appr_purify)
    mods["rodimus_dash_purify"] = statmod_purify
    appears["appr_rodimus_purify"] = appr_purify

    # 2. ID 2798: M2/L2 命中 50% 驱散近战增益，50% 驱散护甲增益
    m_null1, a_null1 = make_nullify_statmod(
        mod_id="rodimus_melee_nullify_melee",
        chance=0.50,
        trigger="onHit",
        trigger_scope="level=Medium,Light",
        appr_id="appr_rodimus_nullify",
        callout_text="驱散",
        target_categories=["attack_buff"],
    )
    m_null2, a_null2 = make_nullify_statmod(
        mod_id="rodimus_melee_nullify_armor",
        chance=0.50,
        trigger="onHit",
        trigger_scope="level=Medium,Light",
        appr_id="appr_rodimus_nullify",
        callout_text="驱散",
        target_categories=["armor_up"],
    )
    mods.update(m_null1)
    mods.update(m_null2)
    appears.update(a_null1)
    appears.update(a_null2)

    # 3. ID 2801: 重击命中施加破甲 (15% 强度，7s，基准 1 层，Native C 负责按增益计数动态倍增)
    m_break, a_break = make_armor_break_statmod(
        mod_id="rodimus_heavy_armor_break",
        duration=7.0,
        break_amount=0.15,
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Heavy",
        appr_id="appr_rodimus_armor_break",
        callout_text="破甲",
        stackable=True,
    )
    mods.update(m_break)
    appears.update(a_break)

    return mods, appears, buffs
