#!/usr/bin/env python3
"""
Bot Ability Implementation: 阿尔茜 (Arcee)
=========================================
Bot ID: arcee_gs_deluxe2014
阵营: 汽车人 (Autobot) | 职业: 侦察兵 (Scout)

【官方技能真理源对照 (来自 character_abilities 数据库)】：
-----------------------------------------------------------------------------
1. [被动 - 爆头 / Head Shot]
   - 官方描述: "远距离攻击有 50% 几率造成爆头，立刻造成 60% 攻击力，并在 3 秒内造成相当于 60% 攻击力的流血伤害。"
   - 实现方案:
     a) arcee_headshot_direct: 触发 onCrit，限制 level=Ranged,Special1，造成 60% ATK 额外直伤。
     b) arcee_headshot_dot: 触发 onCrit，限制 level=Ranged,Special1 且目标非冲刺 (opponent:state!=Dash,Run)，
        造成 60% ATK 流血伤害持续 3.0 秒。呼出文字: "BLEED"。

2. [被动 - 冲锋反制 / Headshot Rush]
   - 官方描述: "对处于前冲或奔跑状态的敌人造成爆头时，100% 造成极速流血。"
   - 实现方案:
     c) arcee_headshot_rush: 触发 onCrit，限制 level=Ranged,Special1 且目标正在冲刺 (opponent:state=Dash,Run)，
        100% 概率施加 3 秒流血。呼出文字: "HEADSHOT"。

3. [特殊技 2 - 致命核心 / Special Attack 2 Bleed]
   - 官方描述: "提高远程伤害与射速，并造成持续 4 秒相当于 108% 攻击力的流血伤害。"
   - 实现方案:
     d) arcee_s2_bleed: 触发 onCrit，限制 level=Special2，造成 108% ATK 流血伤害持续 4.0 秒。呼出文字: "BLEED"。
-----------------------------------------------------------------------------
"""

from ..core import make_bleed_statmod, make_direct_dmg_statmod
from ..registry import register_bot

BOT_ID = "arcee_gs_deluxe2014"


@register_bot(BOT_ID, name_zh="阿尔茜", desc="侦察兵，爆头直伤与流血、冲锋反制")
def build_arcee_abilities(base_hp: float = 34850.0, base_atk: float = 3485.0):
    """
    根据基准属性生成阿尔茜全部专属能力修饰器。
    基准 5星50级 ATK = 3485.0
    """
    mods = {}
    appears = {}
    buffs = {
        # 阿尔茜爆头即时直接伤害 (Direct instant damage)
        "dmg_direct": {
            "id": "dmg_direct",
            "iconTexture": "",
            "image": "",
            "images3": False,
            "modeAvail": [],
            "scope": "global",
            "valueType": "absolute",
            "displayValue": 2091.0,
            "c": 1,
            "value": 2091.0,
            "buffType": "damage",
            "group": "dmg_direct",
            "p": {"damage_type": "bleed"},
            "hasDuration": True,
            "e": 0,
            "time": {"amount": 0.5},
            "loc_name": "headshot_direct",
            "loc_desc": "headshot_direct",
        },
        # 阿尔茜爆头流血 3 秒 DOT (3.0s Bleed DOT)
        "dmg_bleed": {
            "id": "dmg_bleed",
            "iconTexture": "",
            "image": "",
            "images3": False,
            "modeAvail": [],
            "scope": "global",
            "valueType": "absolute",
            "displayValue": 2091.0,
            "c": 1,
            "value": 2091.0,
            "buffType": "damage",
            "group": "dmg_bleed",
            "p": {"damage_type": "bleed"},
            "hasDuration": True,
            "e": 0,
            "time": {"amount": 3.0},
            "loc_name": "bleed",
            "loc_desc": "bleed",
        },
        # 阿尔茜 S2 暴击流血 4 秒 DOT (4.0s Bleed DOT)
        "dmg_bleed_s2": {
            "id": "dmg_bleed_s2",
            "iconTexture": "",
            "image": "",
            "images3": False,
            "modeAvail": [],
            "scope": "global",
            "valueType": "absolute",
            "displayValue": 3764.0,
            "c": 1,
            "value": 3764.0,
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

    # 1. 爆头直接扣血 (60% ATK: 3485 * 0.6 = 2091)
    m1, a1 = make_direct_dmg_statmod(
        mod_id="arcee_headshot_direct",
        dmg=base_atk * 0.60,
        chance=0.5,
        trigger="onCrit",
        trigger_scope="level=Ranged,Special1",
        buff_id="dmg_direct",
    )
    mods.update(m1)
    appears.update(a1)

    # 2. 爆头流血 3 秒 DOT (60% ATK: 3485 * 0.6 = 2091, 50% 几率, 敌非前冲状态)
    m2, a2 = make_bleed_statmod(
        mod_id="arcee_headshot_dot",
        duration=3.0,
        total_dmg=base_atk * 0.60,
        chance=0.5,
        trigger="onCrit",
        trigger_scope="level=Ranged,Special1;opponent:state!=Dash,Run",
        appr_id="appr_arcee_bleed",
        callout_text="BLEED",
        buff_id="dmg_bleed",
    )
    mods.update(m2)
    appears.update(a2)

    # 3. 爆头冲锋反制 3 秒流血 (60% ATK, 100% 必发, 敌处于 Dash/Run 状态)
    m3, a3 = make_bleed_statmod(
        mod_id="arcee_headshot_rush",
        duration=3.0,
        total_dmg=base_atk * 0.60,
        chance=1.0,
        trigger="onCrit",
        trigger_scope="level=Ranged,Special1;opponent:state=Dash,Run",
        appr_id="appr_arcee_headshot",
        callout_text="HEADSHOT",
        buff_id="dmg_bleed",
    )
    mods.update(m3)
    appears.update(a3)

    # 4. S2 暴击流血 4 秒 DOT (108% ATK: 3485 * 1.08 = 3764, 100% 几率)
    m4, a4 = make_bleed_statmod(
        mod_id="arcee_s2_bleed",
        duration=4.0,
        total_dmg=float(round(base_atk * 1.08)),
        chance=1.0,
        trigger="onCrit",
        trigger_scope="level=Special2",
        appr_id="appr_arcee_bleed",
        callout_text="BLEED",
        buff_id="dmg_bleed",
    )
    mods.update(m4)
    appears.update(a4)

    return mods, appears, buffs
