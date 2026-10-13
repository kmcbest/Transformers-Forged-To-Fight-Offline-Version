#!/usr/bin/env python3
"""
Bot Ability Implementation: G1 铁皮 (Ironhide G1)
=================================================
Bot ID: ironhide_gs_kabam
阵营: 汽车人 (Autobot) | 职业: 爆破系 (Demolition)

【官方技能真理源对照 (来自 Upstash KV 聚合 Priorities 清单)】：
-----------------------------------------------------------------------------
1. [SP1 - 近战增益] (ID: 2628, pua_icon: 0xe412)
   - 技能结束后获得1层近战增益，增加35%的近战伤害，持续8秒。
2. [SP2 - 不可阻挡] (ID: 2630, pua_icon: 0xe915)
   - 技能结束后获得7秒的不可阻挡增益。
3. [SP2 - 护甲增益] (ID: 2631, pua_icon: 0xe517)
   - 不可阻挡结束后，获得3层护甲增益，每层4%，持续10秒。
4. [被动 - 护甲增益] (ID: 2632, pua_icon: 0xe517)
   - 开场后获得5层护甲增益，每层4%，持续10秒。
-----------------------------------------------------------------------------
"""

from ..core import (
    make_attack_boost_statmod,
    make_armor_up_statmod,
    make_unstoppable_statmod,
)
from ..registry import register_bot

BOT_ID = "ironhide_gs_kabam"


@register_bot(BOT_ID, name_zh="G1铁皮", desc="爆破系装甲老兵，开局多层厚重护甲，SP1高额近战增益，SP2连续霸体与护甲轮转")
def build_ironhide_gs_abilities(base_hp: float = 32000.0, base_atk: float = 2400.0):
    mods = {}
    appears = {}

    # 1. SP1 近战增益 (ID: 2628): 结束获得 35% 近战增益 8s
    m_sp1, a_sp1 = make_attack_boost_statmod(
        mod_id="ironhide_sp1_melee_buff",
        duration=8.0,
        attack_bonus=0.35,
        chance=1.0,
        trigger="onSpecial1Expiry",
        appr_id="appr_ironhide_sp1_melee_buff",
        callout_text="近战增益",
        show_callout=True,
        pua_icon="\uE412",
    )
    mods.update(m_sp1)
    appears.update(a_sp1)

    # 2. SP2 不可阻挡 (ID: 2630): 结束获得 7s 霸体
    m_sp2_u, a_sp2_u = make_unstoppable_statmod(
        mod_id="ironhide_sp2_unstoppable",
        duration=7.0,
        trigger="onSpecial2Expiry",
        appr_id="appr_ironhide_sp2_unstoppable",
        callout_text="不可阻挡",
        show_callout=True,
        pua_icon="\uE915",
    )
    mods.update(m_sp2_u)
    appears.update(a_sp2_u)

    # 3. SP2 护甲增益 (ID: 2631): 霸体结束后获得 3 层 4% 护甲 10s
    m_sp2_arm, a_sp2_arm = make_armor_up_statmod(
        mod_id="ironhide_sp2_armor_up",
        duration=10.0,
        armor_bonus=0.12,  # 3层各4% = 12%
        chance=1.0,
        trigger="onSpecial2Expiry",
        appr_id="appr_ironhide_sp2_armor_up",
        callout_text="护甲",
        show_callout=True,
        pua_icon="\uE517",
        stackable=True,
        max_stacks=3,
    )
    mods.update(m_sp2_arm)
    appears.update(a_sp2_arm)

    # 4. 被动开场护甲 (ID: 2632): 开局获得 5 层 4% 护甲 10s
    m_p_arm, a_p_arm = make_armor_up_statmod(
        mod_id="ironhide_passive_armor_up",
        duration=10.0,
        armor_bonus=0.20,  # 5层各4% = 20%
        chance=1.0,
        trigger="always",
        appr_id="appr_ironhide_passive_armor_up",
        callout_text="护甲",
        show_callout=True,
        pua_icon="\uE517",
        stackable=True,
        max_stacks=5,
    )
    mods.update(m_p_arm)
    appears.update(a_p_arm)

    return mods, appears
