#!/usr/bin/env python3
"""
Bot Ability Implementation: 酸雨 (Acid Storm)
============================================
Bot ID: acidstorm_gs_leader2015
阵营: 霸天虎 (Decepticon) | 职业: 科技系 (Tech)

【官方技能真理源对照 (来自 Upstash KV 聚合清单)】：
-----------------------------------------------------------------------------
1. [基础 - 强酸喷射与飞溅] (ID: 3566, 3567, category: basic)
   - 官方描述: "远程攻击与重击向敌人喷射强腐蚀性酸液，施加强酸 (Acid Burn)，每秒溶解敌方护甲并造成持续伤害。受到近战物理攻击时，25% 几率将强酸飞溅至攻击者身上，削减其护甲评级。"
   - 实现方案:
     a) acidstorm_ranged_acid: 远程攻击施加 4 秒酸化 DOT (35% ATK, PUA: \\uE524)。
     b) acidstorm_splash_break: 受击 25% 概率飞溅 15% 破甲 5 秒 (PUA: \\uE516)。

2. [被动 - 酸化侵蚀与酸蚀增伤] (ID: 3568, pua_icon: 0xe524, category: passive)
   - 官方描述: "远程攻击与重击命中时有 35% 概率施加一层酸化减益，造成攻击力 35% 的伤害，持续 5 秒，并施加 10% 的破甲减益，持续 5 秒（上限 3 层）。当敌方身上存在酸化减益时，酸雨的所有攻击造成的伤害增加 20%。"
   - 实现方案:
     a) acidstorm_heavy_acid: 重击命中 35% 几率施加 5 秒酸化 (35% ATK, PUA: \\uE524)。
     b) acidstorm_heavy_acid_break: 重击命中 35% 几率施加 10% 破甲 5 秒 (PUA: \\uE516)。
     c) acidstorm_acid_atk_boost: 敌方酸化时酸雨增伤 20% (PUA: \\uE406)。

3. [觉醒技 - 酸性气溶胶护盾] (ID: 3569, pua_icon: 0xe515, category: signature)
   - 官方描述: "战斗开始时以及施放特殊攻击后，酸雨周身环绕酸性气溶胶 5 秒。冷凝为酸性护盾增益（单次受击伤害限制为对手攻击力的 70%，被击中消耗护盾反击酸化减益）。"
   - 实现方案:
     a) acidstorm_sig_aerosol_shield: 开局与特技获得酸性护盾 (PUA: \\uE515)，受击截断 70% 敌方攻击。
     b) acidstorm_sig_shield_counter: 受击消耗护盾反击一层酸化减益 (PUA: \\uE524)。

4. [SP1 - 强酸喷雾] (ID: 3570, pua_icon: 0xe524, category: sp1)
   - 官方描述: "最后一击命中 70% 几率施加一层酸化减益，造成攻击力 40% 的伤害，持续 4 秒。"
   - 实现方案:
     acidstorm_sp1_acid: 最后一击 70% 几率施加 4 秒酸化 (40% ATK, PUA: \\uE524)。

5. [SP2 - 硫酸洪流] (ID: 3571, pua_icon: 0xe516, category: sp2)
   - 官方描述: "每一击有 70% 几率施加一层酸化减益，造成攻击力 50% 的伤害，持续 5 秒；并有 45% 概率施加 20% 的破甲减益，持续 6 秒。"
   - 实现方案:
     a) acidstorm_sp2_acid: 每一击 70% 几率施加 5 秒酸化 (50% ATK, PUA: \\uE524)。
     b) acidstorm_sp2_break: 45% 几率施加 20% 破甲 6 秒 (PUA: \\uE516)。

6. [SP3 - 暴雨倾盆] (ID: 3572, pua_icon: 0xe524, category: sp3)
   - 官方描述: "最后一击 100% 几率施加 2 层酸化减益，造成攻击力 80% 的伤害，持续 6.5 秒；并施加 30% 的破甲减益，持续 8 秒。"
   - 实现方案:
     a) acidstorm_sp3_acid: 最后一击 100% 施加 6.5 秒高浓度酸化 (80% ATK, PUA: \\uE524)。
     b) acidstorm_sp3_break: 施加 30% 破甲 8 秒 (PUA: \\uE516)。
-----------------------------------------------------------------------------
"""

from typing import Dict, Any, Tuple
from ..core import (
    AbilityColor,
    make_burn_statmod,
    make_armor_break_statmod,
    make_attack_boost_statmod,
    make_statmod_appearance,
    validate_appear,
    validate_statmod,
)
from ..registry import register_bot

BOT_ID = "acidstorm_gs_leader2015"


@register_bot(BOT_ID, name_zh="酸雨", desc="科技系腐蚀掌控者，远程强酸侵蚀破甲、受击强酸飞溅反制、酸性气溶胶防护盾与SP2/SP3暴雨消融")
def build_acidstorm_abilities(base_hp: float = 33000.0, base_atk: float = 2380.0) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    mods = {}
    appears = {}

    # 1. 基础远程强酸喷射 (ID: 3566)
    acid_ranged_dmg = base_atk * 0.35
    m_ranged_acid, a_ranged_acid = make_burn_statmod(
        mod_id="acidstorm_ranged_acid",
        duration=4.0,
        total_dmg=acid_ranged_dmg,
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Ranged",
        callout_text="强酸喷射",
        pua_icon="\uE524",
        color_hex=AbilityColor.GREEN_HEALTH_TC,
        gradient_bottom=AbilityColor.GREEN_HEALTH_GB,
    )
    mods.update(m_ranged_acid)
    appears.update(a_ranged_acid)

    # 基础近战受击强酸飞溅破甲 (ID: 3567)
    m_splash_break, a_splash_break = make_armor_break_statmod(
        mod_id="acidstorm_splash_break",
        duration=5.0,
        break_amount=0.15,
        chance=0.25,
        trigger="onPlayerHit",
        trigger_scope="level=Light,Medium,Heavy",
        callout_text="强酸飞溅",
        pua_icon="\uE516",
    )
    mods.update(m_splash_break)
    appears.update(a_splash_break)

    # 2. 被动: 重击酸化侵蚀与破甲 (ID: 3568)
    acid_heavy_dmg = base_atk * 0.35
    m_heavy_acid, a_heavy_acid = make_burn_statmod(
        mod_id="acidstorm_heavy_acid",
        duration=5.0,
        total_dmg=acid_heavy_dmg,
        chance=0.35,
        trigger="onHit",
        trigger_scope="level=Heavy",
        callout_text="酸化侵蚀",
        pua_icon="\uE524",
        color_hex=AbilityColor.GREEN_HEALTH_TC,
        gradient_bottom=AbilityColor.GREEN_HEALTH_GB,
    )
    mods.update(m_heavy_acid)
    appears.update(a_heavy_acid)

    m_heavy_break, a_heavy_break = make_armor_break_statmod(
        mod_id="acidstorm_heavy_acid_break",
        duration=5.0,
        break_amount=0.10,
        chance=0.35,
        trigger="onHit",
        trigger_scope="level=Heavy",
        callout_text="酸蚀破甲",
        pua_icon="\uE516",
    )
    mods.update(m_heavy_break)
    appears.update(a_heavy_break)

    # 敌方酸化时酸雨增伤 20% (ID: 3568)
    m_acid_boost, a_acid_boost = make_attack_boost_statmod(
        mod_id="acidstorm_acid_atk_boost",
        duration=5.0,
        attack_bonus=0.20,
        chance=1.0,
        trigger="onHit",
        trigger_scope="opp.status=dmg_burn",
        callout_text="酸蚀增伤",
        pua_icon="\uE406",
        stackable=False,
        max_stacks=1,
    )
    mods.update(m_acid_boost)
    appears.update(a_acid_boost)

    # 3. 觉醒技: 酸性气溶胶护盾 (ID: 3569)
    appr_aerosol = make_statmod_appearance(
        appr_id="appr_acidstorm_aerosol_shield",
        callout_text="气溶胶护盾",
        desc="酸性气溶胶冷凝为护盾，单次受击伤害上限截断为对手攻击力的 70%",
        pua_icon="\uE515",
        color=AbilityColor.GREEN_HEALTH,
        show_callout=True,
    )
    validate_appear(appr_aerosol)
    appears[appr_aerosol["id"]] = appr_aerosol

    mod_aerosol = {
        "id": "acidstorm_sig_aerosol_shield",
        "t": "signature",
        "ta": "self",
        "tr": ["onStart"],
        "trs": "",
        "uit": [],
        "c": 1.0,
        "d": -1.0,
        "m": 0.0,
        "v": "",
        "ms": "",
        "st": 3,
        "g": "",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": [appr_aerosol["id"]],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
        "eff": [{"t": "damage_cap", "v": 0.70}],
    }
    validate_statmod(mod_aerosol)
    mods[mod_aerosol["id"]] = mod_aerosol

    # 4. SP1 强酸喷雾 (ID: 3570)
    acid_sp1_dmg = base_atk * 0.40
    m_sp1_acid, a_sp1_acid = make_burn_statmod(
        mod_id="acidstorm_sp1_acid",
        duration=4.0,
        total_dmg=acid_sp1_dmg,
        chance=0.70,
        trigger="onHit",
        trigger_scope="level=Special1",
        callout_text="强酸喷雾",
        pua_icon="\uE524",
        color_hex=AbilityColor.GREEN_HEALTH_TC,
        gradient_bottom=AbilityColor.GREEN_HEALTH_GB,
    )
    mods.update(m_sp1_acid)
    appears.update(a_sp1_acid)

    # 5. SP2 硫酸洪流与破甲 (ID: 3571)
    acid_sp2_dmg = base_atk * 0.50
    m_sp2_acid, a_sp2_acid = make_burn_statmod(
        mod_id="acidstorm_sp2_acid",
        duration=5.0,
        total_dmg=acid_sp2_dmg,
        chance=0.70,
        trigger="onHit",
        trigger_scope="level=Special2",
        callout_text="硫酸洪流",
        pua_icon="\uE524",
        color_hex=AbilityColor.GREEN_HEALTH_TC,
        gradient_bottom=AbilityColor.GREEN_HEALTH_GB,
    )
    mods.update(m_sp2_acid)
    appears.update(a_sp2_acid)

    m_sp2_break, a_sp2_break = make_armor_break_statmod(
        mod_id="acidstorm_sp2_break",
        duration=6.0,
        break_amount=0.20,
        chance=0.45,
        trigger="onHit",
        trigger_scope="level=Special2",
        callout_text="强酸溶解",
        pua_icon="\uE516",
    )
    mods.update(m_sp2_break)
    appears.update(a_sp2_break)

    # 6. SP3 暴雨倾盆与破甲 (ID: 3572)
    acid_sp3_dmg = base_atk * 0.80
    m_sp3_acid, a_sp3_acid = make_burn_statmod(
        mod_id="acidstorm_sp3_acid",
        duration=6.5,
        total_dmg=acid_sp3_dmg,
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Special3",
        callout_text="暴雨倾盆",
        pua_icon="\uE524",
        color_hex=AbilityColor.GREEN_HEALTH_TC,
        gradient_bottom=AbilityColor.GREEN_HEALTH_GB,
    )
    mods.update(m_sp3_acid)
    appears.update(a_sp3_acid)

    m_sp3_break, a_sp3_break = make_armor_break_statmod(
        mod_id="acidstorm_sp3_break",
        duration=8.0,
        break_amount=0.30,
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Special3",
        callout_text="骨甲消融",
        pua_icon="\uE516",
    )
    mods.update(m_sp3_break)
    appears.update(a_sp3_break)

    return mods, appears
