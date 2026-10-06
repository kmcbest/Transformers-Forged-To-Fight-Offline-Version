#!/usr/bin/env python3
"""
Bot Ability Implementation: 犀牛 (Rhinox)
=========================================
Bot ID: rhinox_gs_voyager2014
阵营: 巨无霸 (Maximal) / 汽车人 (Autobot) | 职业: 科技系 (Tech)

【官方技能真理源对照 (来自在线优先实现)】：
-----------------------------------------------------------------------------
1. [被动 - 远程流血 / Ranged Bleed] (pua_icon: 0xe401)
   - 描述: "远程攻击30%几率触发流血，造成攻击力60%的伤害，持续5秒"
   - 实现方案: make_bleed_statmod(trigger="onHit", trigger_scope="level=Ranged", chance=0.30, duration=5.0, total_dmg=0.60*ATK)

2. [SP1 - 驱散 / Nullify] (pua_icon: 0xe950, 招式: 戈尔战术)
   - 描述: "100%几率破坏目标的武器系统，驱散最多1个近战、远程或特殊伤害增益。"
   - 实现方案: make_nullify_statmod(trigger="onSpecial1Activate", target_categories=["melee", "ranged", "special"], max_stacks_per_cat=1)

3. [SP1 - 驱散转流血 / Bleed on Nullify] (pua_icon: 0xe401)
   - 描述: "该方式下每次移除增益都有100%几率触发流血，施加攻击力120%的流血伤害，持续14秒。"
   - 实现方案: make_bleed_statmod(trigger="onSpecial1Activate", duration=14.0, total_dmg=1.20*ATK, chance=1.0)

4. [SP2 - 末日之机关枪流血 / Chainguns of Doom Bleed]
   - 描述: "40%概率触发流血，施加攻击力60%的伤害，持续8秒"
   - 实现方案: make_bleed_statmod(trigger="onSpecial2Activate", chance=0.40, duration=8.0, total_dmg=0.60*ATK)
-----------------------------------------------------------------------------
"""

from ..core import make_bleed_statmod, make_nullify_statmod
from ..registry import register_bot

BOT_ID = "rhinox_gs_voyager2014"


@register_bot(BOT_ID, name_zh="犀牛", desc="科技系重装，加特林机关枪持续流血、戈尔战术驱散增益并转化为超长流血")
def build_rhinox_abilities(base_hp: float = 37703.0, base_atk: float = 2187.0):
    """
    根据基准属性生成犀牛全部专属能力修饰器。
    基准 5星50级 HP=37703, ATK = 2187.0
    """
    mods = {}
    appears = {}
    buffs = {}

    # 1. 被动远程流血：远程攻击 30% 几率造成 5 秒 60% ATK 流血
    m_rb, a_rb = make_bleed_statmod(
        mod_id="rhinox_ranged_bleed",
        duration=5.0,
        total_dmg=float(round(base_atk * 0.60)),
        chance=0.30,
        trigger="onHit",
        trigger_scope="level=Ranged",
        appr_id="appr_rhinox_ranged_bleed",
        callout_text="BLEED",
        pua_icon="\uE401",
        buff_id="dmg_bleed",
    )
    mods.update(m_rb)
    appears.update(a_rb)

    # 2. SP1 驱散 (Nullify)：100% 几率驱散目标近战、远程、特殊增益各最多 1 层
    m_null, a_null = make_nullify_statmod(
        mod_id="rhinox_sp1_nullify",
        target_categories=["melee", "ranged", "special"],
        max_stacks_per_cat=1,
        chance=1.0,
        trigger="onSpecial1Activate",
        appr_id="appr_rhinox_sp1_nullify",
        callout_text="NULLIFY",
        pua_icon="\uE950",
        color_hex="38BDF8",
        gradient_bottom="0284C7",
    )
    mods.update(m_null)
    appears.update(a_null)

    # 3. SP1 驱散转流血：每次移除增益触发 14 秒 120% ATK 强力流血
    m_nb, a_nb = make_bleed_statmod(
        mod_id="rhinox_sp1_nullify_bleed",
        duration=14.0,
        total_dmg=float(round(base_atk * 1.20)),
        chance=1.0,
        trigger="onSpecial1Activate",
        appr_id="appr_rhinox_nullify_bleed",
        callout_text="BLEED",
        pua_icon="\uE401",
        buff_id="dmg_bleed",
    )
    mods.update(m_nb)
    appears.update(a_nb)

    # 4. SP2 末日之机关枪流血：40% 概率触发 8 秒 60% ATK 流血
    m_sp2, a_sp2 = make_bleed_statmod(
        mod_id="rhinox_sp2_bleed",
        duration=8.0,
        total_dmg=float(round(base_atk * 0.60)),
        chance=0.40,
        trigger="onSpecial2Activate",
        appr_id="appr_rhinox_sp2_bleed",
        callout_text="BLEED",
        pua_icon="\uE401",
        buff_id="dmg_bleed",
    )
    mods.update(m_sp2)
    appears.update(a_sp2)

    return mods, appears, buffs
