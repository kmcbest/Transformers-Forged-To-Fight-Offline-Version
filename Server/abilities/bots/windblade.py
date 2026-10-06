#!/usr/bin/env python3
"""
Bot Ability Implementation: 风刃 (Windblade)
===========================================
Bot ID: windblade_gs
阵营: 汽车人 (Autobot) | 职业: 侦察兵 (Scout)

【官方技能真理源对照 (来自 windblade_gs.json)】：
-----------------------------------------------------------------------------
1. [被动 - 流血 / Bleed] (pua_icon: 0xe401, category: passive)
   - 官方描述: "近战（包括近战普通攻击和重击）出暴击时，有66%的概率触发流程，造成攻击力68%的伤害，持续4秒。"
   - 实现方案:
     windblade_crit_bleed: 触发 onCrit，限制 level=Melee,Heavy，造成 68% ATK 流血伤害持续 4.0 秒。呼出文字: "BLEED"。
-----------------------------------------------------------------------------
"""

from ..core import make_bleed_statmod
from ..registry import register_bot

BOT_ID = "windblade_gs"


@register_bot(BOT_ID, name_zh="风刃", desc="侦察兵，近战暴击流血")
def build_windblade_abilities(base_hp: float = 26794.0, base_atk: float = 2583.0):
    """
    根据基准属性生成风刃专属流血能力修饰器。
    基准 5星50级 ATK = 2583.0
    """
    mods = {}
    appears = {}

    total_bleed_dmg = float(round(base_atk * 0.68, 2))

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
            "time": {"amount": 4.0},
            "loc_name": "bleed",
            "loc_desc": "bleed",
        },
    }

    # 近战（包括普通攻击和重击）暴击流血 4 秒 DOT (68% ATK, 66% 概率)
    m1, a1 = make_bleed_statmod(
        mod_id="windblade_crit_bleed",
        duration=4.0,
        total_dmg=total_bleed_dmg,
        chance=0.66,
        trigger="onCrit",
        trigger_scope="level=Light,Medium,Heavy",
        appr_id="appr_windblade_bleed",
        callout_text="流血",
        buff_id="dmg_bleed",
    )
    mods.update(m1)
    appears.update(a1)

    return mods, appears, buffs
