#!/usr/bin/env python3
"""
Bot Ability Implementation: 雷震 (Bludgeon)
===========================================
Bot ID: bludgeon_gs_rd20
阵营: 霸天虎 (Decepticon) | 职业: 格斗系 (Warrior)

【官方技能真理源对照 (来自 bludgeon_gs_rd20.json)】：
-----------------------------------------------------------------------------
1. [被动 - 剑刃攻击 / Blade Attacks] (pua_icon: 0xe401, category: passive)
   - 官方描述: "暴击时有25%的概率触发流血，在5秒内造成攻击力120%的伤害。如果是特殊技中的剑刃暴击，概率+60%。"
   - 实现方案:
     a) bludgeon_normal_crit_bleed: 普通暴击 (level!=Special1,Special2,Special3)，25% 几率触发 5 秒 120% ATK 流血。呼出文字: "BLEED"。
     b) bludgeon_sp_crit_bleed: 特殊技剑刃暴击 (level=Special1,Special2,Special3)，85% (25%+60%) 几率触发 5 秒 120% ATK 流血。呼出文字: "BLEED"。
-----------------------------------------------------------------------------
"""

from ..core import make_bleed_statmod
from ..registry import register_bot

BOT_ID = "bludgeon_gs_rd20"


@register_bot(BOT_ID, name_zh="雷震", desc="格斗系，普攻与特殊技暴击流血")
def build_bludgeon_abilities(base_hp: float = 31468.0, base_atk: float = 2491.0):
    """
    根据基准属性生成雷震专属流血能力修饰器。
    基准 5星50级 ATK = 2491.0
    """
    mods = {}
    appears = {}

    total_bleed_dmg = float(round(base_atk * 1.20, 2))

    buffs = {
        "dmg_bleed": {
            "id": "dmg_bleed",
            "iconTexture": "",
            "image": "",
            "images3": False,
            "modeAvail": [],
            "scope": "global",
            "valueType": "absolute",
            "displayValue": total_bleed_dmg,
            "c": 1,
            "value": total_bleed_dmg,
            "buffType": "damage",
            "group": "dmg_bleed",
            "p": {"damage_type": "bleed"},
            "hasDuration": True,
            "e": 0,
            "time": {"amount": 5.0},
            "loc_name": "bleed",
            "loc_desc": "bleed",
        },
    }

    # 1. 常规暴击流血 (25% 几率, 5 秒 120% ATK)
    m1, a1 = make_bleed_statmod(
        mod_id="bludgeon_normal_crit_bleed",
        duration=5.0,
        total_dmg=total_bleed_dmg,
        chance=0.25,
        trigger="onCrit",
        trigger_scope="level=Light,Medium,Heavy",
        appr_id="appr_bludgeon_bleed",
        callout_text="BLEED",
        buff_id="dmg_bleed",
    )
    mods.update(m1)
    appears.update(a1)

    # 2. 特殊技暴击流血 (85% 几率, 5 秒 120% ATK)
    m2, a2 = make_bleed_statmod(
        mod_id="bludgeon_sp_crit_bleed",
        duration=5.0,
        total_dmg=total_bleed_dmg,
        chance=0.85,
        trigger="onCrit",
        trigger_scope="level=Special1,Special2,Special3",
        appr_id="appr_bludgeon_bleed",
        callout_text="BLEED",
        buff_id="dmg_bleed",
    )
    mods.update(m2)
    appears.update(a2)

    return mods, appears, buffs
