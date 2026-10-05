#!/usr/bin/env python3
"""
Bot Ability Implementation: 碎骨魔 (Bonecrusher)
===============================================
Bot ID: bonecrusher_cin_rotf
阵营: 霸天虎 (Decepticon) | 职业: 格斗系 (Warrior)

【官方技能真理源对照 (来自 bonecrusher_cin_rotf.json)】：
-----------------------------------------------------------------------------
1. [被动 - 反暴流血 / Bleed when crit-hit] (pua_icon: 0xe401, category: passive)
   - 官方描述: "受到近战暴击时：90%的几率给对方施加流血，造成攻击力89.6%的伤害，持续7秒，可叠加。"
   - 实现方案:
     bonecrusher_struck_crit_bleed: 触发 onStruckCrit，限制 level=Melee，作用于 opponent，
     造成 89.6% ATK 流血伤害持续 7.0 秒。呼出文字: "BLEED"。

2. [被动 - 重击 / Heavy Attacks] (pua_icon: 0xe401, category: passive)
   - 官方描述: "70%几率触发流血，造成攻击力45%的伤害，持续5.6秒。"
   - 实现方案:
     bonecrusher_heavy_bleed: 触发 onHit，限制 level=Heavy，造成 45% ATK 流血伤害持续 5.6 秒。呼出文字: "BLEED"。
-----------------------------------------------------------------------------
"""

from ..core import make_bleed_statmod
from ..registry import register_bot

BOT_ID = "bonecrusher_cin_rotf"


@register_bot(BOT_ID, name_zh="碎骨魔", desc="格斗系，受近战暴击反击流血与重击流血")
def build_bonecrusher_abilities(base_hp: float = 31468.0, base_atk: float = 2398.0):
    """
    根据基准属性生成碎骨魔专属流血能力修饰器。
    基准 5星50级 ATK = 2398.0
    """
    mods = {}
    appears = {}

    struck_bleed_dmg = float(round(base_atk * 0.896, 2))
    heavy_bleed_dmg = float(round(base_atk * 0.45, 2))

    buffs = {
        # 受到近战暴击施加的 7 秒流血
        "dmg_bleed": {
            "id": "dmg_bleed",
            "iconTexture": "",
            "image": "",
            "images3": False,
            "modeAvail": [],
            "scope": "global",
            "valueType": "absolute",
            "displayValue": struck_bleed_dmg,
            "c": 1,
            "value": struck_bleed_dmg,
            "buffType": "damage",
            "group": "dmg_bleed",
            "p": {"damage_type": "bleed"},
            "hasDuration": True,
            "e": 0,
            "time": {"amount": 7.0},
            "loc_name": "bleed",
            "loc_desc": "bleed",
        },
        # 重击施加的 5.6 秒流血
        "dmg_bleed_heavy": {
            "id": "dmg_bleed_heavy",
            "iconTexture": "",
            "image": "",
            "images3": False,
            "modeAvail": [],
            "scope": "global",
            "valueType": "absolute",
            "displayValue": heavy_bleed_dmg,
            "c": 1,
            "value": heavy_bleed_dmg,
            "buffType": "damage",
            "group": "dmg_bleed",
            "p": {"damage_type": "bleed"},
            "hasDuration": True,
            "e": 0,
            "time": {"amount": 5.6},
            "loc_name": "bleed",
            "loc_desc": "bleed",
        },
    }

    # 1. 受到近战暴击施加流血 7 秒 DOT (89.6% ATK, 90% 几率, 作用于 opponent, 可叠加)
    m1, a1 = make_bleed_statmod(
        mod_id="bonecrusher_struck_crit_bleed",
        duration=7.0,
        total_dmg=struck_bleed_dmg,
        chance=0.90,
        trigger="onStruckCrit",
        trigger_scope="level=Light,Medium,Heavy",
        appr_id="appr_bonecrusher_bleed",
        callout_text="BLEED",
        stackable=True,
        buff_id="dmg_bleed",
        target_actor="opponent",
    )
    mods.update(m1)
    appears.update(a1)

    # 2. 重击命中流血 5.6 秒 DOT (45% ATK, 70% 几率)
    m2, a2 = make_bleed_statmod(
        mod_id="bonecrusher_heavy_bleed",
        duration=5.6,
        total_dmg=heavy_bleed_dmg,
        chance=0.70,
        trigger="onHit",
        trigger_scope="level=Heavy",
        appr_id="appr_bonecrusher_bleed",
        callout_text="BLEED",
        buff_id="dmg_bleed_heavy",
    )
    mods.update(m2)
    appears.update(a2)

    return mods, appears, buffs
