#!/usr/bin/env python3
"""
Bot Ability Implementation: 黄蜂勇士 (Waspinator)
===============================================
Bot ID: waspinator_gs_deluxe
阵营: 原始兽 (Predacon) | 职业: 破坏系 (Demolition)

【官方技能真理源对照 (来自 Upstash KV 聚合 Priorities 清单)】：
-----------------------------------------------------------------------------
1. [SP3 - 燃烧 / Stinger Blast Burn] (ID: 3470, pua_icon: 0xe41d, category: sp3)
   - 官方描述: "100%概率施加燃烧，造成攻击力100%的伤害，持续5秒。"

2. [觉醒技 - 狂怒射击 / Ranged Speed Buff] (ID: 3471, pua_icon: 0xe41b, category: signature)
   - 官方描述: "体力少于50%时，远程攻击速度提升50%。"

3. [被动 - 远程增益 / Low HP Ranged Speed] (ID: 3472, pua_icon: 0xe41b, category: passive)
   - 官方描述: "体力少于50%时，获得远程增益，远程攻击速度提升50%。"

4. [被动 - 垂死狂暴 / Critical Special Damage] (ID: 3473, pua_icon: 0xe41c, category: passive)
   - 官方描述: "生命值小于25%时，获得30%的永久特殊技伤害。"

5. [被动 - 抗性减益 / Resistance Debuff on Attacks] (ID: 3474, pua_icon: 0xe60a, category: passive)
   - 官方描述: "普通远程攻击命中对手施加30%抗性减益(2秒)，重击命中施加30%抗性减益(5秒)。"

6. [特殊技 1 - 暴击几率 / SP1 Crit Rate] (ID: 3475, pua_icon: 0xe40d, category: sp1)
   - 官方描述: "45%的概率得到暴击几率增益，提升30%的暴击几率，持续4秒。"

7. [特殊技 1 - 规避克制 / SP1 Anti-Evade] (ID: 3476, pua_icon: 0xe92a, category: sp1)
   - 官方描述: "施加规避克制，降低对手30%的规避概率，持续4秒。"

8. [特殊技 2 - 抗性削弱 / SP2 Resistance Debuff] (ID: 3477, pua_icon: 0xe60a, category: sp2)
   - 官方描述: "最后一击施加一层30%的抗性减益，持续5秒。"
-----------------------------------------------------------------------------
"""

from ..core import (
    make_burn_statmod,
    make_ranged_boost_statmod,
    make_armor_break_statmod,
    make_crit_rate_statmod,
    validate_color_code,
    validate_statmod,
    validate_appear,
)
from ..registry import register_bot

BOT_ID = "waspinator_gs_deluxe"


@register_bot(BOT_ID, name_zh="黄蜂勇士", desc="破坏系空战毒刺，残血极速射击、垂死特殊技暴走、抗性剥离与规避压制、SP3重炮致命燃烧")
def build_waspinator_abilities(base_hp: float = 29598.0, base_atk: float = 2191.0):
    mods = {}
    appears = {}
    buffs = {}

    # -------------------------------------------------------------------------
    # 1. SP3 燃烧 (ID: 3470): 100% ATK, 5s, 100%
    # -------------------------------------------------------------------------
    m1, a1 = make_burn_statmod(
        mod_id="waspinator_s3_burn",
        duration=5.0,
        total_dmg=float(round(base_atk * 1.00)),
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Special3;dmgFlags=LastHit",
        callout_text="燃烧",
        stackable=True,
        pua_icon="\uE41D",
    )
    mods.update(m1)
    appears.update(a1)

    # -------------------------------------------------------------------------
    # 2. 觉醒技 - 远程射速增益 (ID: 3471): HP < 50% 射速 +50%
    # -------------------------------------------------------------------------
    m_sig_rng, a_sig_rng = make_ranged_boost_statmod(
        mod_id="waspinator_sig_ranged_speed",
        duration=0.0,
        speed_bonus=0.50,
        trigger="always",
        trigger_scope="hp<=0.50",
        appr_id="appr_waspinator_sig_ranged",
        callout_text="远程增益",
        pua_icon="\uE41B",
        color_hex="FF8800",
        gradient_bottom="D97706",
    )
    mods.update(m_sig_rng)
    appears.update(a_sig_rng)

    # -------------------------------------------------------------------------
    # 3. 被动 - 远程射速增益 (ID: 3472): HP < 50% 获得远程增益
    # -------------------------------------------------------------------------
    m_pass_rng, a_pass_rng = make_ranged_boost_statmod(
        mod_id="waspinator_passive_ranged_speed",
        duration=0.0,
        speed_bonus=0.50,
        trigger="always",
        trigger_scope="hp<=0.50",
        appr_id="appr_waspinator_pass_ranged",
        callout_text="远程增益",
        pua_icon="\uE41B",
        color_hex="FF8800",
        gradient_bottom="D97706",
    )
    mods.update(m_pass_rng)
    appears.update(a_pass_rng)

    # -------------------------------------------------------------------------
    # 4. 被动 - 垂死特殊伤害 (ID: 3473): HP < 25% 永久特殊技伤害 +30%
    # -------------------------------------------------------------------------
    validate_color_code("FF8800", "wasp_sp_tc")
    validate_color_code("D97706", "wasp_sp_gb")
    appr_sp_dmg = {
        "id": "appr_waspinator_sp_dmg",
        "a": "特殊伤害",
        "s": "特殊伤害",
        "l": "生命值低于25%时获得30%特殊技伤害加成",
        "ss": "特殊伤害",
        "t": "\uE41C",
        "f": "",
        "st": "特殊伤害",
        "ps": "特殊伤害",
        "pl": "特殊伤害生效中",
        "tc": "FF8800",
        "gt": "FF8800",
        "gb": "D97706",
    }
    validate_appear(appr_sp_dmg)
    appears["appr_waspinator_sp_dmg"] = appr_sp_dmg

    mod_sp_dmg = {
        "id": "waspinator_low_hp_sp_dmg",
        "t": "special_damage",
        "tm": "",
        "tr": ["always"],
        "uit": ["always"],
        "pri": 0,
        "trm": 0.0,
        "trs": "hp<=0.25",
        "trr": "repeat",
        "c": 1.0,
        "m": 1.30,
        "d": -1.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "special_damage",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_waspinator_sp_dmg"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_sp_dmg)
    mods["waspinator_low_hp_sp_dmg"] = mod_sp_dmg

    # -------------------------------------------------------------------------
    # 5. 被动 - 抗性减益 (ID: 3474): 远程命中削弱 30% (2s), 重击命中削弱 30% (5s)
    # -------------------------------------------------------------------------
    m_rng_res, a_rng_res = make_armor_break_statmod(
        mod_id="waspinator_ranged_resist_debuff",
        duration=2.0,
        break_amount=0.30,
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Ranged",
        appr_id="appr_waspinator_ranged_resist",
        callout_text="抗性削减",
        pua_icon="\uE60A",
        color_hex="EF4444",
        gradient_bottom="B91C1C",
    )
    mods.update(m_rng_res)
    appears.update(a_rng_res)

    m_hvy_res, a_hvy_res = make_armor_break_statmod(
        mod_id="waspinator_heavy_resist_debuff",
        duration=5.0,
        break_amount=0.30,
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Heavy",
        appr_id="appr_waspinator_heavy_resist",
        callout_text="抗性削减",
        pua_icon="\uE60A",
        color_hex="EF4444",
        gradient_bottom="B91C1C",
    )
    mods.update(m_hvy_res)
    appears.update(a_hvy_res)

    # -------------------------------------------------------------------------
    # 6. 特殊技 1 - 暴击几率增益 4.0s (ID: 3475): 45% 几率 +30% 暴击
    # -------------------------------------------------------------------------
    m_sp1_crit, a_sp1_crit = make_crit_rate_statmod(
        mod_id="waspinator_sp1_crit_rate",
        duration=4.0,
        crit_bonus=0.30,
        chance=0.45,
        trigger="onSpecial1Activate",
        appr_id="appr_waspinator_sp1_crit",
        callout_text="暴击几率",
        pua_icon="\uE40D",
        color_hex="FF8800",
        gradient_bottom="D97706",
    )
    mods.update(m_sp1_crit)
    appears.update(a_sp1_crit)

    # -------------------------------------------------------------------------
    # 7. 特殊技 1 - 规避克制 4.0s (ID: 3476): 削弱目标 30% 规避率
    # -------------------------------------------------------------------------
    validate_color_code("EF4444", "anti_evade_tc")
    validate_color_code("B91C1C", "anti_evade_gb")
    appr_anti_evade = {
        "id": "appr_waspinator_anti_evade",
        "a": "规避克制",
        "s": "规避克制",
        "l": "降低对手规避几率30%",
        "ss": "规避克制",
        "t": "\uE92A",
        "f": "",
        "st": "规避克制",
        "ps": "规避克制",
        "pl": "规避克制生效中",
        "tc": "EF4444",
        "gt": "EF4444",
        "gb": "B91C1C",
    }
    validate_appear(appr_anti_evade)
    appears["appr_waspinator_anti_evade"] = appr_anti_evade

    mod_anti_evade = {
        "id": "waspinator_sp1_anti_evade",
        "t": "anti_evade",
        "tm": "",
        "tr": ["onSpecial1Hit"],
        "uit": ["onSpecial1Hit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "dmgFlags=LastHit",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.30,
        "d": 4.0,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "anti_evade",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_waspinator_anti_evade"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_anti_evade)
    mods["waspinator_sp1_anti_evade"] = mod_anti_evade

    # -------------------------------------------------------------------------
    # 8. 特殊技 2 - 抗性削弱 5.0s (ID: 3477): 最后一击施加 30% 抗性减益
    # -------------------------------------------------------------------------
    m_sp2_res, a_sp2_res = make_armor_break_statmod(
        mod_id="waspinator_sp2_resist_debuff",
        duration=5.0,
        break_amount=0.30,
        chance=1.0,
        trigger="onSpecial2Hit",
        trigger_scope="dmgFlags=LastHit",
        appr_id="appr_waspinator_sp2_resist",
        callout_text="抗性削减",
        pua_icon="\uE60A",
        color_hex="EF4444",
        gradient_bottom="B91C1C",
    )
    mods.update(m_sp2_res)
    appears.update(a_sp2_res)

    return mods, appears, buffs
