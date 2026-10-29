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

2. [SP1 - 驱散 / Nullify] (pua_icon: 0xe950, 招式: 戈尔战术)
   - 描述: "100%几率破坏目标的武器系统，驱散最多1个近战、远程或特殊伤害增益。"

3. [SP1 - 驱散转流血 / Bleed on Nullify] (pua_icon: 0xe401)
   - 描述: "该方式下每次移除增益都有100%几率触发流血，施加攻击力120%的流血伤害，持续14秒。"

4. [SP2 - 末日之机关枪流血 / Chainguns of Doom Bleed]
   - 描述: "40%概率触发流血，施加攻击力60%的伤害，持续8秒"

5. [被动 - 护盾增益 / Shield Buffs] (ID: 2769, pua_icon: 0xe515)
   - 描述: "开局6个护盾增益限制单次承伤上限，减少35%燃烧与震击伤害，受击或格挡近战消耗，消耗殆尽后8秒充能刷新。"

6. [被动 - 流血增伤 / Bleed Melee Boost] (ID: 2774)
   - 描述: "基本近战攻击：对流血状态的敌人额外造成20%的伤害。"

7. [觉醒技 - 超频 / Overclock] (ID: 2779, pua_icon: 0xe914)
   - 描述: "护盾进一步限制伤害上限至60%，若受创超标则对攻击者反噬160% ATK 震击持续4秒。"

8. [特殊技 3 - 末日机枪流血 / SP3 Chainguns of Doom Bleed] (ID: 2792, pua_icon: 0xe401)
   - 描述: "30%概率触发流血，施加攻击力45%的伤害，持续12秒，敌方高血量时获得额外伤害加成。"
-----------------------------------------------------------------------------
"""

from ..core import (
    make_bleed_statmod,
    make_nullify_statmod,
    make_armor_up_statmod,
    make_attack_boost_statmod,
    make_shock_statmod,
)
from ..registry import register_bot

BOT_ID = "rhinox_gs_voyager2014"


@register_bot(BOT_ID, name_zh="犀牛", desc="科技系重装，加特林机关枪持续流血、戈尔战术驱散转化流血、重装护盾与超频电磁反制")
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
        callout_text="流血",
        pua_icon="\uE401",
        buff_id="dmg_bleed",
    )
    mods.update(m_rb)
    appears.update(a_rb)

    # 2. SP1 驱散 (Nullify)：SP1 命中 100% 几率驱散目标近战、远程、特殊增益各最多 1 层
    m_null, a_null = make_nullify_statmod(
        mod_id="rhinox_sp1_nullify",
        target_categories=["melee", "ranged", "special"],
        max_stacks_per_cat=1,
        chance=1.0,
        trigger="onSpecial1Hit",
        trigger_scope="",
        appr_id="appr_rhinox_sp1_nullify",
        callout_text="驱散",
        pua_icon="\uE950",
        color_hex="38BDF8",
        gradient_bottom="0284C7",
    )
    mods.update(m_null)
    appears.update(a_null)

    # 3. SP1 驱散转流血：SP1 命中移除增益时触发 14 秒 120% ATK 强力流血
    m_nb, a_nb = make_bleed_statmod(
        mod_id="rhinox_sp1_nullify_bleed",
        duration=14.0,
        total_dmg=float(round(base_atk * 1.20)),
        chance=1.0,
        trigger="onSpecial1Hit",
        trigger_scope="",
        appr_id="appr_rhinox_nullify_bleed",
        callout_text="流血",
        pua_icon="\uE401",
        buff_id="dmg_bleed",
    )
    mods.update(m_nb)
    appears.update(a_nb)

    # 4. SP2 末日之机关枪流血：SP2 命中 40% 概率触发 8 秒 60% ATK 流血
    m_sp2, a_sp2 = make_bleed_statmod(
        mod_id="rhinox_sp2_bleed",
        duration=8.0,
        total_dmg=float(round(base_atk * 0.60)),
        chance=0.40,
        trigger="onSpecial2Hit",
        trigger_scope="",
        appr_id="appr_rhinox_sp2_bleed",
        callout_text="流血",
        pua_icon="\uE401",
        buff_id="dmg_bleed",
    )
    mods.update(m_sp2)
    appears.update(a_sp2)

    # 5. 被动 - 护盾增益 (ID: 2769): 6 层护盾提供减伤保护
    m_shield, a_shield = make_armor_up_statmod(
        mod_id="rhinox_shield_buff",
        duration=-1.0,
        armor_bonus=0.20,
        chance=1.0,
        trigger="always",
        trigger_scope="",
        appr_id="appr_rhinox_shield_buff",
        callout_text="护盾",
        pua_icon="\uE515",
        color_hex="29EBF4",
        gradient_bottom="00C5E8",
        stackable=True,
        max_stacks=6,
    )
    mods.update(m_shield)
    appears.update(a_shield)

    # 6. 被动 - 流血增伤 (ID: 2774): 近战对流血目标造成 20% 额外近战伤害
    m_extra_dmg, a_extra_dmg = make_attack_boost_statmod(
        mod_id="rhinox_bleed_extra_dmg",
        duration=0.0,
        attack_bonus=0.20,
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Light,Medium,Heavy;target_has_bleed=True",
        appr_id="appr_rhinox_bleed_extra_dmg",
        callout_text="",
        show_callout=False,
    )
    mods.update(m_extra_dmg)
    appears.update(a_extra_dmg)

    # 7. 觉醒技 - 超频震击 (ID: 2779): 受创过高反弹 160% ATK 震击 4s
    m_overclock, a_overclock = make_shock_statmod(
        mod_id="rhinox_overclock_shock",
        duration=4.0,
        total_dmg=float(round(base_atk * 1.60)),
        chance=1.0,
        trigger="onHitTaken",
        trigger_scope="",
        appr_id="appr_rhinox_overclock_shock",
        callout_text="超频震击",
        pua_icon="\uE914",
        color_hex="EF4444",
        gradient_bottom="B91C1C",
    )
    mods.update(m_overclock)
    appears.update(a_overclock)

    # 8. 特殊技 3 - 流血 (ID: 2792): 30% 几率 12 秒 45% ATK 流血
    m_sp3_bleed, a_sp3_bleed = make_bleed_statmod(
        mod_id="rhinox_sp3_bleed",
        duration=12.0,
        total_dmg=float(round(base_atk * 0.45)),
        chance=0.30,
        trigger="onSpecial3Hit",
        trigger_scope="dmgFlags=LastHit",
        appr_id="appr_rhinox_sp3_bleed",
        callout_text="流血",
        pua_icon="\uE401",
        buff_id="dmg_bleed",
    )
    mods.update(m_sp3_bleed)
    appears.update(a_sp3_bleed)

    return mods, appears, buffs
