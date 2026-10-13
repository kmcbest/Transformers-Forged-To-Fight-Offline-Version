#!/usr/bin/env python3
"""
Bot Ability Implementation: 飞过山/横炮兄弟 - 飞毛腿 (Sunstreaker Deluxe 2008)
==========================================================================
Bot ID: sunstreaker_gs_deluxe2008
职业: 侦察系 (Scout)

【官方技能真理源对照 (来自 Upstash KV 聚合 72 Priorities 清单)】：
-----------------------------------------------------------------------------
1. [被动 - 能量获取 / Power Gain] (ID: 2835, pua_icon: 0xe403, category: passive)
   - 官方描述: "L4或者M2命中对手的时候，在1秒内获得最大能量槽的5%。"
2. [被动 - 近战增益 / Melee Buff] (ID: 2836, pua_icon: 0xe406, category: passive)
   - 官方描述: "重击发起时，有30%的概率获得14%的近战增益，持续5秒"
3. [被动 - 不可阻抗 / Unstoppable] (ID: 2837, pua_icon: 0xe915, category: passive)
   - 官方描述: "生命值掉到40%以下时，得到5秒的不可阻挡增益。"
-----------------------------------------------------------------------------
"""

from ..core import (
    make_attack_boost_statmod,
    make_unstoppable_statmod,
    validate_statmod,
    validate_appear,
)
from ..registry import register_bot

BOT_ID = "sunstreaker_gs_deluxe2008"


@register_bot(BOT_ID, name_zh="飞毛腿", desc="侦察系，连招回能、重击近战增益与残血霸体")
def build_sunstreaker_abilities(base_hp: float = 30000.0, base_atk: float = 3000.0):
    mods = {}
    appears = {}
    buffs = {}

    # 1. ID 2835: L4/M2 命中 1秒内获得 5% 能量
    appr_power = {
        "id": "appr_sunstreaker_power",
        "a": "能量获取",
        "s": "",
        "l": "获得能量",
        "ss": "获得能量",
        "t": "\uE403",
        "f": "",
        "st": "能量获取",
        "ps": "能量获取",
        "pl": "能量获取中",
        "tc": "00CCFF",
        "gt": "00CCFF",
        "gb": "0066CC",
    }
    statmod_power = {
        "id": "sunstreaker_combo_power_gain",
        "t": "power_gain",
        "tm": "",
        "tr": ["onHit"],
        "uit": ["onHit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "level=Light,Medium",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.05,
        "d": 1.0,
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
        "a": ["appr_sunstreaker_power"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(statmod_power)
    validate_appear(appr_power)
    mods["sunstreaker_combo_power_gain"] = statmod_power
    appears["appr_sunstreaker_power"] = appr_power

    # 2. ID 2836: 重击发起 30% 概率获得 14% 近战增益 5.0s
    m_melee, a_melee = make_attack_boost_statmod(
        mod_id="sunstreaker_heavy_melee_buff",
        duration=5.0,
        attack_bonus=0.14,
        chance=0.30,
        trigger="onHit",
        trigger_scope="level=Heavy",
        appr_id="appr_sunstreaker_melee",
        callout_text="近战增益",
        pua_icon="\uE406",
        color_hex="FFAA00",
        stackable=True,
    )
    mods.update(m_melee)
    appears.update(a_melee)

    # 3. ID 2837: 生命值低于 40% 获得 5秒 不可阻挡
    m_unstopp, a_unstopp = make_unstoppable_statmod(
        mod_id="sunstreaker_low_hp_unstoppable",
        duration=5.0,
        trigger="onHealthThreshold",
        trigger_scope="hp_threshold=0.40",
        appr_id="appr_sunstreaker_unstoppable",
        callout_text="不可阻挡",
        show_callout=True,
        play_vfx=True,
        pua_icon="\uE915",
        color_hex="FFAA00",
    )
    mods.update(m_unstopp)
    appears.update(a_unstopp)

    return mods, appears, buffs
