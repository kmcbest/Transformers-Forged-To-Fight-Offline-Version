#!/usr/bin/env python3
"""
Bot Ability Implementation: 碾碎器 (Grindor ROTF)
=================================================
Bot ID: grindor_cin_rotf
职业: 格斗系 (Brawler)

【官方技能真理源对照 (来自 Upstash KV 聚合 72 Priorities 清单)】：
-----------------------------------------------------------------------------
1. [被动 - 暴击率减益 / Crit Debuff] (ID: 3058, category: passive)
   - 官方描述: "当受到攻击时，有11%概率造成一层暴击率减益，降低对手暴击率40%，持续6秒。"
-----------------------------------------------------------------------------
"""

from ..core import (
    make_armor_up_statmod,
    make_burn_statmod,
    validate_statmod,
    validate_appear,
)
from ..registry import register_bot

BOT_ID = "grindor_cin_rotf"


@register_bot(BOT_ID, name_zh="碾碎器", desc="格斗系巨霸，受击触发敌方暴击率减益")
def build_grindor_abilities(base_hp: float = 30000.0, base_atk: float = 3000.0):
    mods = {}
    appears = {}
    buffs = {}

    # 1. ID 3058: 受击 11% 概率给对手施加暴击率减益 (-40% 暴击率, 6.0s)
    appr_crit_down = {
        "id": "appr_grindor_crit_debuff",
        "a": "暴击削弱",
        "s": "",
        "l": "降低暴击率40%",
        "ss": "暴击削弱",
        "t": "\uE400",
        "f": "",
        "st": "暴击削弱",
        "ps": "暴击削弱",
        "pl": "暴击削弱中",
        "tc": "9900CC",
        "gt": "9900CC",
        "gb": "550088",
    }
    statmod_crit_down = {
        "id": "grindor_struck_crit_debuff",
        "t": "crit_rate_debuff",
        "tm": "",
        "tr": ["onStruck"],
        "uit": ["onStruck"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 0.11,
        "m": -0.40,
        "d": 6.0,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 3,
        "g": "",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_grindor_crit_debuff"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(statmod_crit_down)
    validate_appear(appr_crit_down)
    mods["grindor_struck_crit_debuff"] = statmod_crit_down
    appears["appr_grindor_crit_debuff"] = appr_crit_down

# 2. [既有技能保留] 受击护甲增益 (ID: 3056): 8% 几率获得 41% 减伤护甲 6.0s
    m_armor, a_armor = make_armor_up_statmod(
        mod_id="grindor_hit_armor",
        duration=6.0,
        armor_bonus=0.41,
        chance=0.08,
        trigger="onPreDamage",
        trigger_scope="",
        appr_id="appr_grindor_hit_armor",
        callout_text="护甲",
        show_callout=True,
        pua_icon="\uE517",
        color_hex="29EBF4",
        gradient_bottom="00C5E8",
        stackable=True,
        max_stacks=3,
    )
    mods.update(m_armor)
    appears.update(a_armor)

    # 3. [既有技能保留] 重击暴击燃烧 (ID: 3072): 100% 造成 6.0 秒燃烧 (80% ATK)
    m_burn, a_burn = make_burn_statmod(
        mod_id="grindor_heavy_crit_burn",
        duration=6.0,
        total_dmg=float(round(0.80 * base_atk)),
        chance=1.0,
        trigger="onCrit",
        trigger_scope="level=Heavy",
        appr_id="appr_grindor_heavy_crit_burn",
        callout_text="燃烧",
        pua_icon="\uE41D",
    )
    mods.update(m_burn)
    appears.update(a_burn)

    return mods, appears, buffs

