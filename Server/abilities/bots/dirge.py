#!/usr/bin/env python3
"""
Bot Ability Implementation: 挽歌 (Dirge)
=======================================
Bot ID: dirge_gs_deluxe2008
阵营: 霸天虎 (Decepticon) / 雇佣军 (Mercenary) | 职业: 战士系 (Warrior)

【官方技能真理源对照 (来自 Server/tftf_database.db)】：
-----------------------------------------------------------------------------
1. [被动 - 恐惧 / Fear] (ID: 3038, pua_icon: 0xe907)
   - 敌人开局带着恐惧状态（直接显示红图标，无倒计时）。
   - 敌人用近战轻攻击击中挽歌，有20%的概率驱散自己的恐惧状态，中等攻击则有40%的概率。
2. [被动 - 恐惧阴影 / Fear Influence] (ID: 3039, pua_icon: 0xe907)
   - 如果敌人驱散了恐惧状态，则进入恐惧阴影状态（驱散后红图标变灰图标，可计数叠加）。
   - 此状态下，敌人格挡、后闪或者侧闪累计3次，则又会进入恐惧状态（每次计数器+1，3次后变回红色恐惧图标）。
   - 累计到3次之前只要击中挽歌，则计数器清零重新计数。
3. [觉醒 - 冷酷的嘲讽 / Grim Mockery] (ID: 3025, pua_icon: 0xe406)
   - 如果敌人处于恐惧状态下，使用近战攻击被挽歌闪避，挽歌得到1层60%的攻击力增益，持续5秒（不可叠加，可刷新）。
   - 触发攻击力增益后，对方驱散恐惧的概率降低10%，直到下一次成功驱散恐惧后恢复。
4. [被动 - 恐惧流血 / Bleed by Fear] (ID: 3040, pua_icon: 0xe401)
   - 敌人进入恐惧状态后每10秒被施加1层流血，造成挽歌攻击力145%的伤害，持续2秒。
   - 敌人得到恐惧图标的同时，得到一个灰色的流血图标，倒计时10秒后变红色流血图标并被施加流血。
5. [被动 - 暴击几率 / Crit Rate] (ID: 3041, pua_icon: 0xe40d)
   - 对方处于恐惧状态下时，挽歌的所有攻击提升40%的暴击几率（黄色图标在挽歌一侧，随对方恐惧状态出现和消失）。
6. [被动 - 攻击减益 / Attack Debuff] (ID: 3042, pua_icon: 0xe916)
   - 处于恐惧状态的敌方每次后闪或侧闪，会被施加1层40%的攻击力减益，持续5秒。
7. [被动 - 暴击伤害 / Crit Damage] (ID: 3043, pua_icon: 0xe906)
   - 对方处于流血状态下时，挽歌的所有攻击提升30%的暴击伤害。
8. [被动 - 能量功率 / Power Rate] (ID: 3044, pua_icon: 0xe606)
   - 对方处于流血状态下时，挽歌的所有攻击提升10%的能量功率。
9. [SP1 - 特殊伤害 / Special Damage] (ID: 3045, pua_icon: 0xe41c)
   - 对方处于恐惧状态下时，此技能增加35%的伤害。
10. [SP2 - 燃烧 / Burn] (ID: 3046, pua_icon: 0xe41d)
    - 最后一击命中时施加燃烧，造成攻击力35%的伤害，持续4秒；若敌方处于恐惧，则造成70%伤害持续8秒。
11. [SP3 - 恐惧 / Fear] (ID: 3047, pua_icon: 0xe907)
    - 技能完成后施加30秒的恐惧，此期间内恐惧无法被驱散，流血伤害强度翻倍。
-----------------------------------------------------------------------------
"""

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from ..core import (
    make_attack_boost_statmod,
    make_bleed_statmod,
    make_burn_statmod,
    make_crit_damage_statmod,
    make_crit_rate_statmod,
    validate_color_code,
    validate_statmod,
)
from ..registry import register_bot

BOT_ID = "dirge_gs_deluxe2008"


@register_bot(BOT_ID, name_zh="挽歌", desc="战士系追寻者狂徒，散布恐惧与流血，闪避反制与高额暴击压制")
def build_dirge_abilities(base_hp: float = 44950.0, base_atk: float = 2945.0):
    mods = {}
    appears = {}
    buffs = {}

    # -------------------------------------------------------------------------
    # 1. [被动 - 恐惧] (ID: 3038): 敌人开局常驻恐惧状态，可被近战轻(20%)/中(40%)驱散
    # -------------------------------------------------------------------------
    validate_color_code("EF4444", "dirge_fear_tc")
    validate_color_code("B91C1C", "dirge_fear_gb")
    appr_fear = {
        "id": "appr_dirge_fear",
        "a": "恐惧",
        "s": "恐惧",
        "l": "敌人处于恐惧状态下，攻击力与心理遭受极大压制，并暴露多重战术破绽。",
        "ss": "陷入恐惧",
        "t": "\uE907",
        "f": "",
        "st": "恐惧",
        "ps": "恐惧",
        "pl": "恐惧中",
        "tc": "EF4444",
        "gt": "EF4444",
        "gb": "B91C1C",
    }
    mod_fear = {
        "id": "dirge_fear_debuff",
        "t": "passive",
        "tm": "",
        "tr": ["always"],
        "uit": ["always"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 1.0,
        "d": -1.0,  # 永久常驻状态，由 NativeHook 根据击中概率净化
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 0,
        "g": "dirge_fear",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_dirge_fear"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_fear)
    mods["dirge_fear_debuff"] = mod_fear
    appears["appr_dirge_fear"] = appr_fear

    # -------------------------------------------------------------------------
    # 2. [被动 - 恐惧阴影] (ID: 3039): 驱散后进入阴影，敌人格挡/闪避累计3次重回恐惧
    # -------------------------------------------------------------------------
    validate_color_code("9CA3AF", "dirge_shadow_tc")
    validate_color_code("4B5563", "dirge_shadow_gb")
    appr_shadow = {
        "id": "appr_dirge_fear_shadow",
        "a": "恐惧阴影",
        "s": "",
        "l": "恐惧驱散后的余波，敌人格挡、后闪或侧闪累计3次将再次重陷恐惧。",
        "ss": "恐惧阴影",
        "t": "\uE907",
        "f": "",
        "st": "恐惧阴影",
        "ps": "恐惧阴影",
        "pl": "恐惧阴影笼罩",
        "tc": "9CA3AF",
        "gt": "6B7280",
        "gb": "4B5563",
    }
    mod_shadow = {
        "id": "dirge_fear_shadow",
        "t": "passive",
        "tm": "",
        "tr": [],
        "uit": [],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 1.0,
        "d": -1.0,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 3,
        "g": "dirge_shadow",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_dirge_fear_shadow"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_shadow)
    mods["dirge_fear_shadow"] = mod_shadow
    appears["appr_dirge_fear_shadow"] = appr_shadow

    # -------------------------------------------------------------------------
    # 3. [觉醒 - 冷酷的嘲讽] (ID: 3025): 恐惧下近战被挽歌闪避，+60% 攻击力增益 5s
    # -------------------------------------------------------------------------
    m_sig, a_sig = make_attack_boost_statmod(
        mod_id="dirge_sig_mockery",
        duration=5.0,
        attack_bonus=0.60,
        chance=1.0,
        trigger="onEvade",
        appr_id="appr_dirge_sig_mockery",
        callout_text="冷酷嘲讽",
        show_callout=True,
        pua_icon="\uE406",
        color_hex="F59E0B",
        gradient_bottom="D97706",
        stackable=False,
    )
    mods.update(m_sig)
    appears.update(a_sig)

    # -------------------------------------------------------------------------
    # 4. [被动 - 恐惧流血预备与结算] (ID: 3040): 10s 预备计时 -> 2s 造成 145% ATK 暴烈流血
    # -------------------------------------------------------------------------
    # 4a. 灰色预备流血图标 (10秒周期倒计时)
    appr_b_timer = {
        "id": "appr_dirge_bleed_timer",
        "a": "流血预备",
        "s": "",
        "l": "恐惧加剧倒计时，周期结束将造成大额流血伤害。",
        "ss": "流血倒计时",
        "t": "\uE401",
        "f": "",
        "st": "流血预备",
        "ps": "流血预备",
        "pl": "流血预备中",
        "tc": "9CA3AF",
        "gt": "6B7280",
        "gb": "4B5563",
    }
    mod_b_timer = {
        "id": "dirge_bleed_timer",
        "t": "passive",
        "tm": "",
        "tr": [],
        "uit": [],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 1.0,
        "d": 10.0,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 0,
        "g": "dirge_bleed_timer",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_dirge_bleed_timer"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_b_timer)
    mods["dirge_bleed_timer"] = mod_b_timer
    appears["appr_dirge_bleed_timer"] = appr_b_timer

    # 4b. 红色流血结算: 2秒造成 145% ATK 伤害 (2945 * 1.45 = 4270)
    m_bleed, a_bleed = make_bleed_statmod(
        mod_id="dirge_fear_bleed",
        duration=2.0,
        total_dmg=float(round(base_atk * 1.45)),
        chance=1.0,
        trigger="onHit",
        appr_id="appr_dirge_fear_bleed",
        callout_text="恐惧流血",
        pua_icon="\uE401",
        stackable=True,
    )
    mods.update(m_bleed)
    appears.update(a_bleed)

    # -------------------------------------------------------------------------
    # 5. [被动 - 暴击几率] (ID: 3041): 对方处于恐惧状态下，挽歌攻击提升 40% 暴击率
    # -------------------------------------------------------------------------
    m_crit, a_crit = make_crit_rate_statmod(
        mod_id="dirge_fear_crit_buff",
        duration=-1.0,
        crit_bonus=0.40,
        chance=1.0,
        appr_id="appr_dirge_fear_crit_buff",
        callout_text="暴击提升",
        pua_icon="\uE40D",
        color_hex="F59E0B",
        gradient_bottom="D97706",
    )
    mods.update(m_crit)
    appears.update(a_crit)

    # -------------------------------------------------------------------------
    # 6. [被动 - 攻击减益] (ID: 3042): 恐惧敌人每次后闪或侧闪，施加 40% 攻击力减益 5s
    # -------------------------------------------------------------------------
    appr_debuff = {
        "id": "appr_dirge_evade_atk_debuff",
        "a": "攻击减益",
        "s": "",
        "l": "因躲避挽歌追杀而陷入慌乱，攻击力大幅降低40%。",
        "ss": "-40% 攻击力",
        "t": "\uE916",
        "f": "",
        "st": "攻击减益",
        "ps": "攻击减益",
        "pl": "攻击力降低",
        "tc": "EF4444",
        "gt": "EF4444",
        "gb": "B91C1C",
    }
    mod_debuff = {
        "id": "dirge_evade_atk_debuff",
        "t": "passive",
        "tm": "",
        "tr": ["onDodge"],
        "uit": ["onDodge"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": -0.40,
        "d": 5.0,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "dirge_atk_debuff",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_dirge_evade_atk_debuff"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_debuff)
    mods["dirge_evade_atk_debuff"] = mod_debuff
    appears["appr_dirge_evade_atk_debuff"] = appr_debuff

    # -------------------------------------------------------------------------
    # 7. [被动 - 暴击伤害] (ID: 3043): 对方流血状态下，挽歌攻击提升 30% 暴击伤害
    # -------------------------------------------------------------------------
    m_cdmg, a_cdmg = make_crit_damage_statmod(
        mod_id="dirge_bleed_crit_dmg",
        duration=-1.0,
        crit_dmg_bonus=0.30,
        chance=1.0,
        appr_id="appr_dirge_bleed_crit_dmg",
        callout_text="暴伤强化",
        pua_icon="\uE906",
        color_hex="F59E0B",
        gradient_bottom="D97706",
    )
    mods.update(m_cdmg)
    appears.update(a_cdmg)

    # -------------------------------------------------------------------------
    # 8. [被动 - 能量功率] (ID: 3044): 对方流血状态下，挽歌攻击提升 10% 能量功率
    # -------------------------------------------------------------------------
    validate_color_code("8B5CF6", "dirge_power_tc")
    validate_color_code("6D28D9", "dirge_power_gb")
    appr_power = {
        "id": "appr_dirge_bleed_power_rate",
        "a": "能量功率",
        "s": "",
        "l": "汲取对手失血的能量流动，攻击获得的能量功率提升10%。",
        "ss": "+10% 能量功率",
        "t": "\uE606",
        "f": "",
        "st": "能量功率",
        "ps": "能量功率",
        "pl": "能量充沛",
        "tc": "8B5CF6",
        "gt": "7C3AED",
        "gb": "6D28D9",
    }
    mod_power = {
        "id": "dirge_bleed_power_rate",
        "t": "passive",
        "tm": "",
        "tr": [],
        "uit": [],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.10,
        "d": -1.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 0,
        "g": "dirge_power",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_dirge_bleed_power_rate"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_power)
    mods["dirge_bleed_power_rate"] = mod_power
    appears["appr_dirge_bleed_power_rate"] = appr_power

    # -------------------------------------------------------------------------
    # 9. [SP1 - 特殊伤害] (ID: 3045): 敌方恐惧状态下 SP1 伤害增加 35%
    # -------------------------------------------------------------------------
    m_sp1, a_sp1 = make_attack_boost_statmod(
        mod_id="dirge_sp1_fear_boost",
        duration=3.0,
        attack_bonus=0.35,
        chance=1.0,
        trigger="onSpecial1Activate",
        appr_id="appr_dirge_sp1_fear_boost",
        callout_text="特殊伤害",
        show_callout=True,
        pua_icon="\uE41C",
        color_hex="F97316",
        gradient_bottom="C2410C",
    )
    mods.update(m_sp1)
    appears.update(a_sp1)

    # -------------------------------------------------------------------------
    # 10. [SP2 - 燃烧] (ID: 3046): 终结击造成 35% ATK 燃烧 (4s); 恐惧下 70% ATK 燃烧 (8s)
    # -------------------------------------------------------------------------
    # 10a. 普通燃烧 (4s, 35% ATK: 2945 * 0.35 = 1031)
    m_sp2_norm, a_sp2_norm = make_burn_statmod(
        mod_id="dirge_sp2_burn",
        duration=4.0,
        total_dmg=float(round(base_atk * 0.35)),
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Special2;dmgFlags=LastHit",
        appr_id="appr_dirge_sp2_burn",
        callout_text="燃烧",
        show_callout=True,
        pua_icon="\uE41D",
    )
    mods.update(m_sp2_norm)
    appears.update(a_sp2_norm)

    # 10b. 恐惧强化燃烧 (8s, 70% ATK: 2945 * 0.70 = 2062)
    m_sp2_fear, a_sp2_fear = make_burn_statmod(
        mod_id="dirge_sp2_burn_fear",
        duration=8.0,
        total_dmg=float(round(base_atk * 0.70)),
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Special2;dmgFlags=LastHit",
        appr_id="appr_dirge_sp2_burn_fear",
        callout_text="暴烈燃烧",
        show_callout=True,
        pua_icon="\uE41D",
    )
    mods.update(m_sp2_fear)
    appears.update(a_sp2_fear)

    # -------------------------------------------------------------------------
    # 11. [SP3 - 强化恐惧] (ID: 3047): 30s 不可驱散恐惧，流血伤害强度翻倍
    # -------------------------------------------------------------------------
    validate_color_code("FFFFFF", "dirge_sp3_tc")
    validate_color_code("D1D5DB", "dirge_sp3_gb")
    appr_sp3 = {
        "id": "appr_dirge_sp3_fear",
        "a": "终极恐惧",
        "s": "",
        "l": "无处可逃！30秒内恐惧绝对不可驱散，流血伤害强度翻倍！",
        "ss": "不可驱散恐惧",
        "t": "\uE907",
        "f": "",
        "st": "终极恐惧",
        "ps": "终极恐惧",
        "pl": "绝对恐惧中",
        "tc": "FFFFFF",
        "gt": "FFFFFF",
        "gb": "D1D5DB",
    }
    mod_sp3 = {
        "id": "dirge_sp3_fear_empower",
        "t": "passive",
        "tm": "",
        "tr": ["onSpecial3Hit"],
        "uit": ["onSpecial3Hit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 1.0,
        "d": 30.0,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 0,
        "g": "dirge_sp3_fear",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_dirge_sp3_fear"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_sp3)
    mods["dirge_sp3_fear_empower"] = mod_sp3
    appears["appr_dirge_sp3_fear"] = appr_sp3

    return mods, appears, buffs
