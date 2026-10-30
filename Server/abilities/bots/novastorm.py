#!/usr/bin/env python3
"""
Bot Ability Implementation: 新星风 (Nova Storm)
==============================================
Bot ID: novastorm_gs_leader2015
阵营: 霸天虎 (Decepticon) | 职业: 破坏系 (Demolition)

【官方技能真理源对照 (来自 Upstash KV 聚合清单)】：
-----------------------------------------------------------------------------
1. [基础 - 热核弹头] (ID: 3585, category: basic)
   - 官方描述: "远程重火器发射高温热核弹，击中必定引发燃烧 (Burn)，持续造成火热伤害并阻止敌方任何生命恢复。"
   - 实现方案:
     novastorm_ranged_burn: 远程攻击 100% 施加 4 秒燃烧 (40% ATK, PUA: \\uE41D)。

2. [被动 - 爆轰充能与重击烈焰] (ID: 3586, pua_icon: 0xe404, category: passive)
   - 官方描述: "连击计数达到 5 的倍数时，获得一层爆轰增益：使下一次重击必定暴击，并获得 35% 的暴击伤害增益。重击命中 100% 概率施加燃烧减益，造成攻击力 60% 的伤害，持续 5 秒。"
   - 实现方案:
     a) novastorm_combo_crit_rate: 连击达到 5 的倍数获得重击必暴 (PUA: \\uE404)。
     b) novastorm_combo_crit_dmg: 连击达到 5 的倍数获得 35% 暴伤增益 (PUA: \\uE404)。
     c) novastorm_heavy_burn: 重击命中 100% 施加 5 秒燃烧 (60% ATK, PUA: \\uE41D)。

3. [觉醒技 - 热核殉爆] (ID: 3587, pua_icon: 0xe40d, category: signature)
   - 官方描述: "特殊攻击暴击时，引爆目标身上所有的燃烧减益，每层燃烧立即造成攻击力 [30% - 60%] 的瞬时爆发热伤害；如果目标身上没有任何燃烧减益，则立即对其施加一层燃烧减益，造成攻击力 [50% - 100%] 的伤害，持续 5 秒。"
   - 实现方案:
     a) novastorm_sig_detonate: 特技暴击对手处于燃烧时，造成 45% ATK 瞬时爆轰伤害。
     b) novastorm_sig_burn: 特技暴击对手无燃烧时，施加 5 秒 75% ATK 燃烧 (PUA: \\uE40D)。

4. [SP1 - 辐射爆轰] (ID: 3588, pua_icon: 0xe41d, category: sp1)
   - 官方描述: "每一击有 75% 概率施加燃烧减益，造成攻击力 40% 的伤害，持续 4 秒；若发生暴击，额外获得 30% 暴击伤害增益，持续 4 秒。"
   - 实现方案:
     a) novastorm_sp1_burn: 每一击 75% 施加 4 秒燃烧 (40% ATK, PUA: \\uE41D)。
     b) novastorm_sp1_crit_dmg: 暴击额外获得 30% 暴伤 4 秒 (PUA: \\uE404)。

5. [SP2 - 超新星突进] (ID: 3589, pua_icon: 0xe915, category: sp2)
   - 官方描述: "技能激活时获得不可阻挡增益，持续至技能结束。最后一击 100% 概率施加 2 层燃烧减益，造成攻击力 80% 的伤害，持续 6 秒。"
   - 实现方案:
     a) novastorm_sp2_unstoppable: 激活获得不可阻挡 (PUA: \\uE915)。
     b) novastorm_sp2_burn: 最后一击 100% 施加 6 秒燃烧 (80% ATK, PUA: \\uE41D)。

6. [SP3 - 恒星坍缩歼灭] (ID: 3590, pua_icon: 0xe404, category: sp3)
   - 官方描述: "最后一击 100% 概率施加 3 层燃烧减益，造成攻击力 120% 的伤害，持续 7 秒；并即时扣除对方最大能量值的 20%。"
   - 实现方案:
     a) novastorm_sp3_burn: 最后一击 100% 施加 7 秒核爆燃烧 (120% ATK, PUA: \\uE404)。
     b) novastorm_sp3_drain: 即时扣除对方能量 (PUA: \\uE607)。
-----------------------------------------------------------------------------
"""

from typing import Dict, Any, Tuple
from ..core import (
    AbilityColor,
    make_burn_statmod,
    make_direct_dmg_statmod,
    make_unstoppable_statmod,
    make_crit_rate_statmod,
    make_crit_damage_statmod,
    make_power_leak_statmod,
)
from ..registry import register_bot

BOT_ID = "novastorm_gs_leader2015"


@register_bot(BOT_ID, name_zh="新星风", desc="破坏系重核巡航者，远程与重击热核燃烧、连招必暴强化、特技暴击引爆烈焰殉爆与SP2霸体轰击")
def build_novastorm_abilities(base_hp: float = 33500.0, base_atk: float = 2450.0) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    mods = {}
    appears = {}

    # 1. 基础远程燃烧 (ID: 3585)
    burn_ranged_dmg = base_atk * 0.40
    m_ranged_burn, a_ranged_burn = make_burn_statmod(
        mod_id="novastorm_ranged_burn",
        duration=4.0,
        total_dmg=burn_ranged_dmg,
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Ranged",
        callout_text="热核燃烧",
        pua_icon="\uE41D",
    )
    mods.update(m_ranged_burn)
    appears.update(a_ranged_burn)

    # 2. 连击 5 倍数重击必暴与暴伤 (ID: 3586)
    m_combo_crit, a_combo_crit = make_crit_rate_statmod(
        mod_id="novastorm_combo_crit_rate",
        duration=6.0,
        crit_bonus=1.0,
        chance=1.0,
        trigger="onComboCount",
        trigger_scope="combo%5==0",
        callout_text="爆轰充能",
        pua_icon="\uE404",
    )
    mods.update(m_combo_crit)
    appears.update(a_combo_crit)

    m_combo_dmg, a_combo_dmg = make_crit_damage_statmod(
        mod_id="novastorm_combo_crit_dmg",
        duration=6.0,
        crit_dmg_bonus=0.35,
        chance=1.0,
        trigger="onComboCount",
        trigger_scope="combo%5==0",
        callout_text="爆轰强化",
        pua_icon="\uE404",
    )
    mods.update(m_combo_dmg)
    appears.update(a_combo_dmg)

    # 重击命中 100% 燃烧 (ID: 3586)
    burn_heavy_dmg = base_atk * 0.60
    m_heavy_burn, a_heavy_burn = make_burn_statmod(
        mod_id="novastorm_heavy_burn",
        duration=5.0,
        total_dmg=burn_heavy_dmg,
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Heavy",
        callout_text="爆轰烈焰",
        pua_icon="\uE41D",
    )
    mods.update(m_heavy_burn)
    appears.update(a_heavy_burn)

    # 3. 觉醒技: 特技暴击引爆/施加燃烧 (ID: 3587)
    detonate_dmg = base_atk * 0.45
    m_sig_detonate, a_sig_detonate = make_direct_dmg_statmod(
        mod_id="novastorm_sig_detonate",
        dmg=detonate_dmg,
        chance=1.0,
        trigger="onCrit",
        trigger_scope="level=Special1,Special2,Special3;opp.status=dmg_burn",
    )
    mods.update(m_sig_detonate)
    appears.update(a_sig_detonate)

    burn_sig_dmg = base_atk * 0.75
    m_sig_burn, a_sig_burn = make_burn_statmod(
        mod_id="novastorm_sig_burn",
        duration=5.0,
        total_dmg=burn_sig_dmg,
        chance=1.0,
        trigger="onCrit",
        trigger_scope="level=Special1,Special2,Special3",
        callout_text="热能引爆",
        pua_icon="\uE40D",
    )
    mods.update(m_sig_burn)
    appears.update(a_sig_burn)

    # 4. SP1 燃烧与暴伤 (ID: 3588)
    burn_sp1_dmg = base_atk * 0.40
    m_sp1_burn, a_sp1_burn = make_burn_statmod(
        mod_id="novastorm_sp1_burn",
        duration=4.0,
        total_dmg=burn_sp1_dmg,
        chance=0.75,
        trigger="onHit",
        trigger_scope="level=Special1",
        callout_text="辐射爆轰",
        pua_icon="\uE41D",
    )
    mods.update(m_sp1_burn)
    appears.update(a_sp1_burn)

    m_sp1_crit_dmg, a_sp1_crit_dmg = make_crit_damage_statmod(
        mod_id="novastorm_sp1_crit_dmg",
        duration=4.0,
        crit_dmg_bonus=0.30,
        chance=1.0,
        trigger="onCrit",
        trigger_scope="level=Special1",
        callout_text="暴伤激增",
        pua_icon="\uE404",
    )
    mods.update(m_sp1_crit_dmg)
    appears.update(a_sp1_crit_dmg)

    # 5. SP2 霸体与燃烧 (ID: 3589)
    m_sp2_unstop, a_sp2_unstop = make_unstoppable_statmod(
        mod_id="novastorm_sp2_unstoppable",
        duration=3.5,
        trigger="onSpecial2Activate",
        callout_text="不可阻挡",
        pua_icon="\uE915",
    )
    mods.update(m_sp2_unstop)
    appears.update(a_sp2_unstop)

    burn_sp2_dmg = base_atk * 0.80
    m_sp2_burn, a_sp2_burn = make_burn_statmod(
        mod_id="novastorm_sp2_burn",
        duration=6.0,
        total_dmg=burn_sp2_dmg,
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Special2",
        callout_text="核热烈焰",
        pua_icon="\uE41D",
    )
    mods.update(m_sp2_burn)
    appears.update(a_sp2_burn)

    # 6. SP3 毁灭燃烧与能量扣除 (ID: 3590)
    burn_sp3_dmg = base_atk * 1.20
    m_sp3_burn, a_sp3_burn = make_burn_statmod(
        mod_id="novastorm_sp3_burn",
        duration=7.0,
        total_dmg=burn_sp3_dmg,
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Special3",
        callout_text="超新星爆发",
        pua_icon="\uE404",
    )
    mods.update(m_sp3_burn)
    appears.update(a_sp3_burn)

    m_sp3_drain, a_sp3_drain = make_power_leak_statmod(
        mod_id="novastorm_sp3_drain",
        duration=1.0,
        drain_bars=0.60,
        chance=1.0,
        trigger="onSpecial3Expiry",
        callout_text="能量湮灭",
        pua_icon="\uE607",
    )
    mods.update(m_sp3_drain)
    appears.update(a_sp3_drain)

    return mods, appears
