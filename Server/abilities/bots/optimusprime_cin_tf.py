#!/usr/bin/env python3
"""
Bot Ability Implementation: 电影擎天柱 (Optimus Prime MV1)
======================================================
Bot ID: optimusprime_cin_tf
阵营: 汽车人 (Autobot) | 职业: 格斗系 (Brawler)

【官方技能真理源对照 (来自 Upstash KV 聚合 Priorities 清单)】：
-----------------------------------------------------------------------------
1. [被动 - 护甲增益 / Armor Buff] (ID: 2724, pua_icon: 0xe517, category: passive)
   - 官方描述: "当进入格挡姿态时，有100%的概率获得护甲增益，降低受到攻击伤害的16.5%，持续7秒。"
   - 实现方案:
     optimusprime_cin_tf_block_armor:
       触发 onPlayerStateEnter, state=Block, 100% 概率获得 7.0 秒护甲增益 (减伤 16.5%),
       作用于 self, 蓝色血条圆环图标 (PUA: 0xe517, Hex: 3B82F6 / 1D4ED8), 呼出文字: "护甲"。

2. [被动 - 近战增益 / Melee Buff] (ID: 2725, pua_icon: 0xe412, category: passive)
   - 官方描述: "所有攻击：10%的概率获得近战增益，提升近战伤害60%，持续4秒。//最大一层，不可叠加，再次获得就刷新当前的"
   - 实现方案:
     optimusprime_cin_tf_melee_buff:
       触发 onHit, 10% 概率获得 4.0 秒近战增益 (+60% 近战伤害),
       作用于 self, 橙红血条圆环图标 (PUA: 0xe412, Hex: F97316 / C2410C), 呼出文字: "近战增益"。

3. [被动 - 意志力 / Willpower] (ID: 2726, pua_icon: 0xe942, category: passive)
   - 官方描述: "如果擎天柱正在流血状态，他将自己造成所有伤害的35%转化为自己的生命值。身上最多只能被施加一层流血，超过一层的流血会被当场净化，并转化为擎天柱最大能量的10%"
   - 实现方案:
     optimusprime_cin_tf_willpower:
       由 Native C (skill_optimus_mv.c) 拦截流血并在施加时净化转能量，吸血回生。

4. [SP1 - 流血 / Bleed] (ID: 2713, pua_icon: 0xe401, category: sp1)
   - 官方描述: "60%概率施加流血，造成攻击力40%的伤害，持续4秒"
   - 实现方案:
     optimusprime_cin_tf_sp1_bleed:
       触发 onSpecial1Hit, 60% 概率施加 4.0 秒流血 (造成 40% ATK 伤害),
       作用于 opponent, 红色血条圆环图标 (PUA: 0xe401, Hex: EF4444 / B91C1C), 呼出文字: "流血"。

5. [SP1 - 伤害增益 / Dynamic Damage Boost] (ID: 2729, pua_icon: 0xe406, category: sp1)
   - 官方描述: "擎天柱失去体力越多，该技能伤害越高，最高增伤150% (50% HP 时增伤 75%)"
   - 实现方案:
     由 Native C (skill_optimus_mv.c) 在 SP1 命中时依据当前血量百分比动态乘以 (1.0 + 1.5 * loss_ratio)。

6. [SP2 - 双剑流血 / Guardian Slash Bleed] (ID: 2727, pua_icon: 0xe401, category: sp2)
   - 官方描述: "前两击每一击有90%概率施加流血，造成攻击力40%的伤害，持续4秒。"
   - 实现方案:
     optimusprime_cin_tf_sp2_bleed:
       触发 onSpecial2Hit, index=0,1 (前两击), 90% 概率施加 4.0 秒流血 (造成 40% ATK 伤害),
       作用于 opponent, 红色血条圆环图标 (PUA: 0xe401, Hex: EF4444 / B91C1C), 呼出文字: "流血"。
-----------------------------------------------------------------------------
"""

from ..core import (
    make_armor_up_statmod,
    make_attack_boost_statmod,
    make_bleed_statmod,
)
from ..registry import register_bot

BOT_ID = "optimusprime_cin_tf"


@register_bot(BOT_ID, name_zh="电影擎天柱", desc="格斗系重装领袖，进入格挡获得护甲增益，攻击触发近战增益，意志力流血净化转能量与吸血，SP1逆境斩击与SP2双剑流血")
def build_optimusprime_cin_tf_abilities(base_hp: float = 29334.0, base_atk: float = 2398.0):
    mods = {}
    appears = {}

    # 1. 被动护甲增益 (ID: 2724): 进入格挡 100% 获得 7s 护甲 (减伤 16.5%)
    m_arm, a_arm = make_armor_up_statmod(
        mod_id="optimusprime_cin_tf_block_armor",
        duration=7.0,
        armor_bonus=0.165,
        chance=1.0,
        trigger="onPlayerStateEnter",
        trigger_scope="state=Block",
        appr_id="appr_optimusprime_cin_tf_block_armor",
        callout_text="护甲",
    )
    mods["optimusprime_cin_tf_block_armor"] = m_arm
    appears["appr_optimusprime_cin_tf_block_armor"] = a_arm

    # 2. 被动近战增益 (ID: 2725): 所有攻击 10% 概率触发 4s 近战增益 (+60% 近战伤害)
    m_atk, a_atk = make_attack_boost_statmod(
        mod_id="optimusprime_cin_tf_melee_buff",
        duration=4.0,
        attack_bonus=0.60,
        chance=0.10,
        trigger="onHit",
        trigger_scope="",
        appr_id="appr_optimusprime_cin_tf_melee_buff",
        callout_text="近战增益",
    )
    mods["optimusprime_cin_tf_melee_buff"] = m_atk
    appears["appr_optimusprime_cin_tf_melee_buff"] = a_atk

    # 3. SP1 流血 (ID: 2713): 60% 几率施加流血 4 秒 (40% ATK 伤害)
    m_sp1_b, a_sp1_b = make_bleed_statmod(
        mod_id="optimusprime_cin_tf_sp1_bleed",
        duration=4.0,
        total_dmg=base_atk * 0.40,
        chance=0.60,
        trigger="onSpecial1Hit",
        trigger_scope=None,
        appr_id="appr_optimusprime_cin_tf_sp1_bleed",
        callout_text="流血",
    )
    mods["optimusprime_cin_tf_sp1_bleed"] = m_sp1_b
    appears["appr_optimusprime_cin_tf_sp1_bleed"] = a_sp1_b

    # 4. SP2 流血 (ID: 2727): 前两击每一击 90% 概率施加流血 4 秒 (40% ATK 伤害)
    m_sp2_b, a_sp2_b = make_bleed_statmod(
        mod_id="optimusprime_cin_tf_sp2_bleed",
        duration=4.0,
        total_dmg=base_atk * 0.40,
        chance=0.90,
        trigger="onSpecial2Hit",
        trigger_scope="index=0,1",
        appr_id="appr_optimusprime_cin_tf_sp2_bleed",
        callout_text="流血",
    )
    mods["optimusprime_cin_tf_sp2_bleed"] = m_sp2_b
    appears["appr_optimusprime_cin_tf_sp2_bleed"] = a_sp2_b

    return mods, appears
