#!/usr/bin/env python3
"""
Bot Ability Implementation: 漂移 (Drift)
=======================================
Bot ID: drift_cin_aoe
阵营: 汽车人 (Autobot) | 职业: 格斗系 (Warrior)

【官方技能真理源对照 (来自 drift_cin_aoe.json)】：
-----------------------------------------------------------------------------
1. [被动 - 剑刃暴击 / Critical Sword Attacks] (pua_icon: 0xe401, category: passive)
   - 官方描述: "近战与远程攻击出暴击时，有65%的概率造成攻击力30%的流血伤害，持续2秒"
   - 实现方案:
     drift_sword_crit_bleed: 触发 onCrit，限制 level=Melee,Ranged，造成 30% ATK 流血伤害持续 2.0 秒。呼出文字: "BLEED"。
-----------------------------------------------------------------------------
"""

from ..core import make_bleed_statmod
from ..registry import register_bot

BOT_ID = "drift_cin_aoe"


@register_bot(BOT_ID, name_zh="漂移", desc="格斗系，近战与远程暴击流血")
def build_drift_abilities(base_hp: float = 30845.0, base_atk: float = 2352.0):
    """
    根据基准属性生成漂移专属流血能力修饰器。
    基准 5星50级 ATK = 2352.0
    """
    mods = {}
    appears = {}

    total_bleed_dmg = float(round(base_atk * 0.30, 2))

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
            "time": {"amount": 2.0},
            "loc_name": "bleed",
            "loc_desc": "bleed",
        },
    }

    # 近战与远程暴击流血 2 秒 DOT (30% ATK, 65% 概率)
    m1, a1 = make_bleed_statmod(
        mod_id="drift_sword_crit_bleed",
        duration=2.0,
        total_dmg=total_bleed_dmg,
        chance=0.65,
        trigger="onCrit",
        trigger_scope="level=Light,Medium,Heavy,Ranged",
        appr_id="appr_drift_bleed",
        callout_text="流血",
        buff_id="dmg_bleed",
    )
    mods.update(m1)
    appears.update(a1)

    return mods, appears, buffs
