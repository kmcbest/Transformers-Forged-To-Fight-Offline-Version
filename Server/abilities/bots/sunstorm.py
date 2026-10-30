#!/usr/bin/env python3
"""
Bot Ability Implementation: 太阳风 (Sunstorm)
============================================
Bot ID: sunstorm_gs_leader2015
阵营: 霸天虎 (Decepticon) | 职业: 格斗系 / 爆破系 (Warrior / Demolition)

【官方技能真理源对照 (来自 Upstash KV 聚合清单)】：
-----------------------------------------------------------------------------
1. [基础 - 白热聚变辐射] (ID: 3594, category: basic)
   - 官方描述: "近战攻击散发白热聚变辐射，刀刀见血，造成辐射撕裂 (Radiation Bleed) 与重度破甲。"
   - 实现方案:
     a) sunstorm_melee_bleed: 近战物理攻击 70% 施加 4 秒流血 DOT (35% ATK, PUA: \\uE401)。
     b) sunstorm_melee_break: 近战物理攻击 40% 施加 15% 破甲 4 秒 (PUA: \\uE516)。

2. [被动 - 聚变燃烧与规避压制] (ID: 3595, pua_icon: 0xe41d, category: passive)
   - 官方描述: "重击命中 100% 概率施加一层燃烧减益，造成攻击力 50% 的伤害，持续 4.5 秒。暴击命中时 50% 概率额外施加一层燃烧减益，造成攻击力 30% 的伤害，持续 4 秒。当对手处于燃烧减益状态时，其规避几率降低 35%。"
   - 实现方案:
     a) sunstorm_heavy_burn: 重击 100% 施加 4.5 秒燃烧 (50% ATK, PUA: \\uE41D)。
     b) sunstorm_crit_burn: 暴击 50% 额外施加 4 秒燃烧 (30% ATK, PUA: \\uE41D)。
     c) sunstorm_burn_anti_evade: 对手燃烧时削弱其 35% 规避率 (PUA: \\uE509)。

3. [觉醒技 - 失控恒星反应堆] (ID: 3596, pua_icon: 0xe412, category: signature)
   - 官方描述: "当生命值高于 40% 时，体内失控的恒星反应堆过热，每秒扣除自身 0.5% 生命值；作为代价，每扣除累计 10% 生命值，获得一层持续到战斗结束的 [10% - 18%] 近战增益（上限 4 层）。当生命值降至 40% 及以下时，停止扣除自身生命值，并保留已获得的全部近战增益。"
   - 实现方案:
     sunstorm_sig_melee_gain: 恒星反应堆过热叠加 15% 近战增益 (上限 4 层, 永久常驻, PUA: \\uE412)。

4. [SP1 - 太阳喷射] (ID: 3597, pua_icon: 0xe41d, category: sp1)
   - 官方描述: "最后一击命中 100% 几率施加一层燃烧减益，造成攻击力 45% 的伤害，持续 4 秒；技能结束后获得一个暴击增益，增加 25% 暴击率，持续 4 秒。"
   - 实现方案:
     a) sunstorm_sp1_burn: 最后一击 100% 施加 4 秒燃烧 (45% ATK, PUA: \\uE41D)。
     b) sunstorm_sp1_crit_buff: 技能结束后提升 25% 暴击率 4 秒 (PUA: \\uE406)。

5. [SP2 - 耀斑轰炸] (ID: 3598, pua_icon: 0xe41d, category: sp2)
   - 官方描述: "最后一击命中 80% 几率施加 2 层燃烧减益，造成攻击力 60% 的伤害，持续 5 秒；并有 50% 概率造成眩晕，持续 1.5 秒。"
   - 实现方案:
     a) sunstorm_sp2_burn: 最后一击 80% 施加 5 秒双层燃烧 (60% ATK, PUA: \\uE41D)。
     b) sunstorm_sp2_stun: 50% 概率造成 1.5 秒眩晕 (PUA: \\uE605)。

6. [SP3 - 日冕风暴] (ID: 3599, pua_icon: 0xe404, category: sp3)
   - 官方描述: "最后一击命中 100% 几率施加 3 层燃烧减益，造成攻击力 90% 的伤害，持续 6 秒；技能结束后获得一个暴击伤害增益，增加 35% 暴击伤害，持续 6 秒。"
   - 实现方案:
     a) sunstorm_sp3_burn: 最后一击 100% 施加 6 秒三层燃烧 (90% ATK, PUA: \\uE404)。
     b) sunstorm_sp3_crit_dmg: 技能结束后提升 35% 暴伤 6 秒 (PUA: \\uE406)。
-----------------------------------------------------------------------------
"""

from typing import Dict, Any, Tuple
from ..core import (
    AbilityColor,
    make_burn_statmod,
    make_bleed_statmod,
    make_armor_break_statmod,
    make_attack_boost_statmod,
    make_crit_rate_statmod,
    make_crit_damage_statmod,
    make_stun_statmod,
    make_statmod_appearance,
    validate_appear,
    validate_statmod,
)
from ..registry import register_bot

BOT_ID = "sunstorm_gs_leader2015"


@register_bot(BOT_ID, name_zh="太阳风", desc="格斗系恒星聚变狂，近战辐射撕裂破甲、恒星反应堆失控换取永久近战叠层、耀斑烈焰与SP3日冕核爆")
def build_sunstorm_abilities(base_hp: float = 34000.0, base_atk: float = 2420.0) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    mods = {}
    appears = {}

    # 1. 基础近战辐射撕裂与破甲 (ID: 3594)
    bleed_melee_dmg = base_atk * 0.35
    m_melee_bleed, a_melee_bleed = make_bleed_statmod(
        mod_id="sunstorm_melee_bleed",
        duration=4.0,
        total_dmg=bleed_melee_dmg,
        chance=0.70,
        trigger="onHit",
        trigger_scope="level=Light,Medium,Heavy",
        callout_text="辐射撕裂",
        pua_icon="\uE401",
    )
    mods.update(m_melee_bleed)
    appears.update(a_melee_bleed)

    m_melee_break, a_melee_break = make_armor_break_statmod(
        mod_id="sunstorm_melee_break",
        duration=4.0,
        break_amount=0.15,
        chance=0.40,
        trigger="onHit",
        trigger_scope="level=Light,Medium,Heavy",
        callout_text="辐射破甲",
        pua_icon="\uE516",
    )
    mods.update(m_melee_break)
    appears.update(a_melee_break)

    # 2. 被动: 重击与暴击燃烧 (ID: 3595)
    burn_heavy_dmg = base_atk * 0.50
    m_heavy_burn, a_heavy_burn = make_burn_statmod(
        mod_id="sunstorm_heavy_burn",
        duration=4.5,
        total_dmg=burn_heavy_dmg,
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Heavy",
        callout_text="聚变燃烧",
        pua_icon="\uE41D",
    )
    mods.update(m_heavy_burn)
    appears.update(a_heavy_burn)

    burn_crit_dmg = base_atk * 0.30
    m_crit_burn, a_crit_burn = make_burn_statmod(
        mod_id="sunstorm_crit_burn",
        duration=4.0,
        total_dmg=burn_crit_dmg,
        chance=0.50,
        trigger="onCrit",
        callout_text="辐射燃烧",
        pua_icon="\uE41D",
    )
    mods.update(m_crit_burn)
    appears.update(a_crit_burn)

    # 对手处于燃烧时规避降低 35% (ID: 3595)
    appr_anti_evade = make_statmod_appearance(
        appr_id="appr_sunstorm_burn_anti_evade",
        callout_text="规避压制",
        desc="对手处于燃烧状态，规避几率降低 35%",
        pua_icon="\uE509",
        color=AbilityColor.RED_DEBUFF,
        show_callout=True,
    )
    validate_appear(appr_anti_evade)
    appears[appr_anti_evade["id"]] = appr_anti_evade

    mod_anti_evade = {
        "id": "sunstorm_burn_anti_evade",
        "t": "passive",
        "ta": "opponent",
        "tr": ["onHit"],
        "trs": "opp.status=dmg_burn",
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
        "a": [appr_anti_evade["id"]],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
        "eff": [{"t": "evade_rate", "v": -0.35}],
    }
    validate_statmod(mod_anti_evade)
    mods[mod_anti_evade["id"]] = mod_anti_evade

    # 3. 觉醒技: 恒星反应堆过热 (ID: 3596) - 永久近战增益 15% 上限 4 层
    m_sig_melee, a_sig_melee = make_attack_boost_statmod(
        mod_id="sunstorm_sig_melee_gain",
        duration=30.0,
        attack_bonus=0.15,
        chance=1.0,
        trigger="onHit",
        trigger_scope="self:health>0.40",
        appr_id="appr_sunstorm_sig_reactor",
        callout_text="恒星过热",
        pua_icon="\uE412",
        stackable=True,
        max_stacks=4,
    )
    mods.update(m_sig_melee)
    appears.update(a_sig_melee)

    # 4. SP1 燃烧与暴击率 (ID: 3597)
    burn_sp1_dmg = base_atk * 0.45
    m_sp1_burn, a_sp1_burn = make_burn_statmod(
        mod_id="sunstorm_sp1_burn",
        duration=4.0,
        total_dmg=burn_sp1_dmg,
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Special1",
        callout_text="太阳喷射",
        pua_icon="\uE41D",
    )
    mods.update(m_sp1_burn)
    appears.update(a_sp1_burn)

    m_sp1_crit, a_sp1_crit = make_crit_rate_statmod(
        mod_id="sunstorm_sp1_crit_buff",
        duration=4.0,
        crit_bonus=0.25,
        chance=1.0,
        trigger="onSpecial1Expiry",
        callout_text="暴击强化",
        pua_icon="\uE406",
    )
    mods.update(m_sp1_crit)
    appears.update(a_sp1_crit)

    # 5. SP2 双层燃烧与眩晕 (ID: 3598)
    burn_sp2_dmg = base_atk * 0.60
    m_sp2_burn, a_sp2_burn = make_burn_statmod(
        mod_id="sunstorm_sp2_burn",
        duration=5.0,
        total_dmg=burn_sp2_dmg,
        chance=0.80,
        trigger="onHit",
        trigger_scope="level=Special2",
        callout_text="耀斑轰炸",
        pua_icon="\uE41D",
    )
    mods.update(m_sp2_burn)
    appears.update(a_sp2_burn)

    m_sp2_stun, a_sp2_stun = make_stun_statmod(
        mod_id="sunstorm_sp2_stun",
        duration=1.5,
        chance=0.50,
        trigger="onHit",
        trigger_scope="level=Special2",
        target="opponent",
        callout_text="眩晕",
        pua_icon="\uE605",
    )
    mods.update(m_sp2_stun)
    appears.update(a_sp2_stun)

    # 6. SP3 日冕风暴与暴伤 (ID: 3599)
    burn_sp3_dmg = base_atk * 0.90
    m_sp3_burn, a_sp3_burn = make_burn_statmod(
        mod_id="sunstorm_sp3_burn",
        duration=6.0,
        total_dmg=burn_sp3_dmg,
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Special3",
        callout_text="日冕风暴",
        pua_icon="\uE404",
    )
    mods.update(m_sp3_burn)
    appears.update(a_sp3_burn)

    m_sp3_crit_dmg, a_sp3_crit_dmg = make_crit_damage_statmod(
        mod_id="sunstorm_sp3_crit_dmg",
        duration=6.0,
        crit_dmg_bonus=0.35,
        chance=1.0,
        trigger="onSpecial3Expiry",
        callout_text="日冕暴伤",
        pua_icon="\uE406",
    )
    mods.update(m_sp3_crit_dmg)
    appears.update(a_sp3_crit_dmg)

    return mods, appears
