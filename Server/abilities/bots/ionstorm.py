#!/usr/bin/env python3
"""
Bot Ability Implementation: 离子风 (Ion Storm)
==============================================
Bot ID: ionstorm_gs_leader2015
阵营: 霸天虎 (Decepticon) | 职业: 科技系 / 战术系 (Tech / Tactician)

【官方技能真理源对照 (来自 Upstash KV 聚合清单)】：
-----------------------------------------------------------------------------
1. [基础 - 高压电离冲击] (ID: 3576, category: basic)
   - 官方描述: "攻击附带高压电离冲击，命中时降低对手能量获取率 35%，并有几率对格斗系敌人的霸体状态造成直接电击打断。"
   - 实现方案:
     ionstorm_ion_impact: 命中降低对手 35% 能量获取率 (PUA: \\uE607)。

2. [被动 - 电离破甲与霸体驱散] (ID: 3577, pua_icon: 0xe516, category: passive)
   - 官方描述: "重击命中 100% 概率首先移除对方身上一层护甲增益，并施加 30% 的破甲减益，持续 6 秒。对手处于破甲减益状态下时，离子风的所有攻击造成额外 25% 的伤害。若对手处于不可阻挡状态，离子风的重击命中 100% 概率驱散其不可阻挡增益。"
   - 实现方案:
     a) ionstorm_heavy_armor_break: 重击命中施加 30% 破甲 6 秒 (PUA: \\uE516)。
     b) ionstorm_heavy_nullify_armor: 重击移除敌方一层护甲增益 (PUA: \\uE950)。
     c) ionstorm_heavy_nullify_unstop: 重击驱散敌方不可阻挡增益 (PUA: \\uE950)。
     d) ionstorm_armor_broken_boost: 对手破甲时离子风所有攻击增伤 25% (PUA: \\uE406)。

3. [觉醒技 - 电磁逆火] (ID: 3578, pua_icon: 0xe914, category: signature)
   - 官方描述: "敌方释放特殊技时，有 [50% - 85%] 几率触发电磁逆火：施加震击减益，造成攻击力 [40% - 80%] 的伤害，持续 5 秒，并扣除对手一格能量的 [20% - 40%]。"
   - 实现方案:
     a) ionstorm_sig_backfire_shock: 敌方释放特技 70% 几率施加 5 秒震击 (60% ATK, PUA: \\uE914)。
     b) ionstorm_sig_backfire_drain: 扣除对手 30% 能量 (PUA: \\uE607)。

4. [SP1 - 高压电弧] (ID: 3579, pua_icon: 0xe914, category: sp1)
   - 官方描述: "最后一击命中 85% 概率施加震击减益，造成攻击力 45% 的伤害，持续 4 秒；对拥有护甲增益或不可阻挡增益的敌人，额外造成 50% 的伤害。"
   - 实现方案:
     a) ionstorm_sp1_shock: 最后一击 85% 概率施加 4 秒震击 (45% ATK, PUA: \\uE914)。
     b) ionstorm_sp1_unstop_punish: 敌方有护甲或霸体时 SP1 增伤 50% (PUA: \\uE406)。

5. [SP2 - 离子风暴] (ID: 3580, pua_icon: 0xe516, category: sp2)
   - 官方描述: "每一击有 90% 概率施加破甲，首先移除对方身上一层护甲增益，并施加 30% 的破甲减益，持续 6 秒；70% 概率追加震击减益，造成攻击力 50% 的伤害，持续 5 秒。"
   - 实现方案:
     a) ionstorm_sp2_break: 每一击 90% 施加 30% 破甲 6 秒 (PUA: \\uE516)。
     b) ionstorm_sp2_shock: 70% 概率追加 5 秒震击 (50% ATK, PUA: \\uE914)。

6. [SP3 - 湮灭电离轰击] (ID: 3581, pua_icon: 0xe516, category: sp3)
   - 官方描述: "最后一击 100% 概率移除对方身上所有护甲增益，并施加一个 40% 的破甲减益，持续 8 秒；技能结束后离子风获得一个攻击增益，增加 30% 的攻击力，持续 6 秒。"
   - 实现方案:
     a) ionstorm_sp3_break: 最后一击 100% 施加 40% 破甲 8 秒 (PUA: \\uE516)。
     b) ionstorm_sp3_atk_buff: 技能结束后自身提升 30% 攻击力 6 秒 (PUA: \\uE406)。
-----------------------------------------------------------------------------
"""

from typing import Dict, Any, Tuple
from ..core import (
    AbilityColor,
    make_shock_statmod,
    make_armor_break_statmod,
    make_attack_boost_statmod,
    make_nullify_statmod,
    make_power_leak_statmod,
    make_statmod_appearance,
    validate_appear,
    validate_statmod,
)
from ..registry import register_bot

BOT_ID = "ionstorm_gs_leader2015"


@register_bot(BOT_ID, name_zh="离子风", desc="科技系电离破坏狂，重击驱散霸体与护盾、特技反制电磁逆火、SP2与SP3终极电弧破甲震击")
def build_ionstorm_abilities(base_hp: float = 34500.0, base_atk: float = 2350.0) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    mods = {}
    appears = {}

    # 1. 基础电离冲击 (ID: 3576): 降低能量获取 35%
    appr_ion_impact = make_statmod_appearance(
        appr_id="appr_ionstorm_ion_impact",
        callout_text="电离冲击",
        desc="电离冲击降低目标 35% 能量获取率",
        pua_icon="\uE607",
        color=AbilityColor.RED_DEBUFF,
        show_callout=True,
    )
    validate_appear(appr_ion_impact)
    appears[appr_ion_impact["id"]] = appr_ion_impact

    mod_ion_impact = {
        "id": "ionstorm_ion_impact",
        "t": "passive",
        "ta": "opponent",
        "tr": ["onHit"],
        "trs": "",
        "uit": [],
        "c": 1.0,
        "d": 4.0,
        "m": 0.0,
        "v": "",
        "ms": "",
        "st": 1,
        "g": "",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": [appr_ion_impact["id"]],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
        "eff": [{"t": "power_gain", "v": -0.35}],
    }
    validate_statmod(mod_ion_impact)
    mods[mod_ion_impact["id"]] = mod_ion_impact

    # 2. 被动: 重击破甲 (ID: 3577)
    m_heavy_break, a_heavy_break = make_armor_break_statmod(
        mod_id="ionstorm_heavy_armor_break",
        duration=6.0,
        break_amount=0.30,
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Heavy",
        callout_text="电离破甲",
        pua_icon="\uE516",
    )
    mods.update(m_heavy_break)
    appears.update(a_heavy_break)

    # 重击驱散护甲与驱散霸体 (ID: 3577)
    m_null_armor, a_null_armor = make_nullify_statmod(
        mod_id="ionstorm_heavy_nullify_armor",
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Heavy;opp.status=armor_up",
        target_buff="armor_up",
        callout_text="护甲破除",
        pua_icon="\uE950",
    )
    mods.update(m_null_armor)
    appears.update(a_null_armor)

    m_null_unstop, a_null_unstop = make_nullify_statmod(
        mod_id="ionstorm_heavy_nullify_unstop",
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Heavy;opp.status=unstoppable",
        target_buff="unstoppable",
        callout_text="霸体破除",
        pua_icon="\uE950",
    )
    mods.update(m_null_unstop)
    appears.update(a_null_unstop)

    # 破甲状态增伤 25% (ID: 3577)
    m_break_boost, a_break_boost = make_attack_boost_statmod(
        mod_id="ionstorm_armor_broken_boost",
        duration=6.0,
        attack_bonus=0.25,
        chance=1.0,
        trigger="onHit",
        trigger_scope="opp.status=armor_break",
        callout_text="电离增伤",
        pua_icon="\uE406",
        stackable=False,
        max_stacks=1,
    )
    mods.update(m_break_boost)
    appears.update(a_break_boost)

    # 3. 觉醒技: 电磁逆火 (ID: 3578)
    shock_sig_dmg = base_atk * 0.60
    m_sig_shock, a_sig_shock = make_shock_statmod(
        mod_id="ionstorm_sig_backfire_shock",
        duration=5.0,
        total_dmg=shock_sig_dmg,
        chance=0.70,
        trigger="onSpecialActivate",
        target="opponent",
        callout_text="电磁逆火",
        pua_icon="\uE914",
    )
    mods.update(m_sig_shock)
    appears.update(a_sig_shock)

    m_sig_drain, a_sig_drain = make_power_leak_statmod(
        mod_id="ionstorm_sig_backfire_drain",
        duration=1.0,
        drain_bars=0.30,
        chance=0.70,
        trigger="onSpecialActivate",
        callout_text="逆火流失",
        pua_icon="\uE607",
    )
    mods.update(m_sig_drain)
    appears.update(a_sig_drain)

    # 4. SP1 震击与增伤 (ID: 3579)
    shock_sp1_dmg = base_atk * 0.45
    m_sp1_shock, a_sp1_shock = make_shock_statmod(
        mod_id="ionstorm_sp1_shock",
        duration=4.0,
        total_dmg=shock_sp1_dmg,
        chance=0.85,
        trigger="onHit",
        trigger_scope="level=Special1",
        callout_text="高压震击",
        pua_icon="\uE914",
    )
    mods.update(m_sp1_shock)
    appears.update(a_sp1_shock)

    m_sp1_punish, a_sp1_punish = make_attack_boost_statmod(
        mod_id="ionstorm_sp1_unstop_punish",
        duration=4.0,
        attack_bonus=0.50,
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Special1",
        callout_text="电离过载",
        pua_icon="\uE406",
        stackable=False,
        max_stacks=1,
    )
    mods.update(m_sp1_punish)
    appears.update(a_sp1_punish)

    # 5. SP2 破甲与震击 (ID: 3580)
    m_sp2_break, a_sp2_break = make_armor_break_statmod(
        mod_id="ionstorm_sp2_break",
        duration=6.0,
        break_amount=0.30,
        chance=0.90,
        trigger="onHit",
        trigger_scope="level=Special2",
        callout_text="离子破甲",
        pua_icon="\uE516",
    )
    mods.update(m_sp2_break)
    appears.update(a_sp2_break)

    shock_sp2_dmg = base_atk * 0.50
    m_sp2_shock, a_sp2_shock = make_shock_statmod(
        mod_id="ionstorm_sp2_shock",
        duration=5.0,
        total_dmg=shock_sp2_dmg,
        chance=0.70,
        trigger="onHit",
        trigger_scope="level=Special2",
        callout_text="离子震击",
        pua_icon="\uE914",
    )
    mods.update(m_sp2_shock)
    appears.update(a_sp2_shock)

    # 6. SP3 终极破甲与增攻 (ID: 3581)
    m_sp3_break, a_sp3_break = make_armor_break_statmod(
        mod_id="ionstorm_sp3_break",
        duration=8.0,
        break_amount=0.40,
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Special3",
        callout_text="湮灭粉碎",
        pua_icon="\uE516",
    )
    mods.update(m_sp3_break)
    appears.update(a_sp3_break)

    m_sp3_atk, a_sp3_atk = make_attack_boost_statmod(
        mod_id="ionstorm_sp3_atk_buff",
        duration=6.0,
        attack_bonus=0.30,
        chance=1.0,
        trigger="onSpecial3Expiry",
        callout_text="电离激增",
        pua_icon="\uE406",
        stackable=False,
        max_stacks=1,
    )
    mods.update(m_sp3_atk)
    appears.update(a_sp3_atk)

    return mods, appears
