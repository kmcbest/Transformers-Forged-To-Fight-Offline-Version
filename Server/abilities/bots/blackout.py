#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bot Ability Implementation: 眩晕 (Blackout)
===========================================
Bot ID: blackout_cin_tf
阵营: 霸天虎 (Decepticon) | 职业: 破坏分子 (Demolitions / demo)
基准数值: HP 40519, ATK 3272

【官方技能真理源对照 (来自 character_abilities 数据库，共 14 条)】：
-----------------------------------------------------------------------------
1. [被动 - 暴击几率 / Crit Rate] (PUA: \uE40D)
   - 连击数每增加5，获得1层12%的暴击几率增益，被敌人命中打断连击时全部移除。

2. [被动 - 无尽怒火 / Infinite Fury] (PUA: \uE906)
   - 当暴击率超过100%时，溢出的每1%暴击率会转化为1%暴击伤害增益，这个增益会在暴击率低于100%时移除。

3. [被动 - 燃烧 / Heavy Attack Burn] (PUA: \uE41D)
   - 重击如果暴击，100%概率造成燃烧，施加攻击力80%的伤害，持续6秒。

4. [特殊技 1 - 能量炮 / SP1 Unblockable & Special Damage Boost] (PUA: \uE41F, \uE41C)
   - 最后1击不可防御 // 最后一击的时间内出现浅紫色图标 (由 skill_blackout.c 精准控制时间窗)
   - 技能期间提升30%的特殊伤害 (SP1 进入挂载，SP1 退出立即移除)。

5. [特殊技 2 - 翼刃回旋 / SP2 Crit Damage & Stackable Bleed] (PUA: \uE906, \uE401)
   - 技能期间提升60%的暴击伤害 (SP2 启动挂载，SP2 退出立即移除)
   - 每1击暴击时有100%的概率触发流血，可叠加，在3秒内造成攻击力60%的伤害。

6. [特殊技 3 - 猎杀 / SP3 Burn & Stackable Permanent Crit Resistance Debuff] (PUA: \uE41D, \uE409)
   - 最后一击的暴击率增加50%，如果暴击，100%概率造成燃烧，施加攻击力80%的伤害，持续6秒。
   - 最后一击命中时，向对手施加1层永久暴击抗性减益，在对手身上打出暴击的几率提升20%。//可叠加 (st=99, 由 SP3 终击或退出结算施加 1 层)

7. [觉醒能力 - 追猎 / I'll Hunt You Down!] (PUA: \uE608)
   - 当眩晕的普通攻击落空时，他猎杀对手的渴望变得更强，获得1层60%的能量功率增益，持续3秒
   - //仅近战、远程、重击落空（未命中且未被防视为落空，排除对波抵消与反射，包含对手前冲穿弹）时触发，
     S技落空不触发。最大1层，再次触发时刷新倒计时。
-----------------------------------------------------------------------------
"""

import sys
try:
    if hasattr(sys.stdout, 'reconfigure') and not sys.stdout.closed:
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure') and not sys.stderr.closed:
        sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

from ..core import (
    AbilityColor,
    make_attack_boost_statmod,
    make_bleed_statmod,
    make_burn_statmod,
    make_crit_rate_statmod,
    make_crit_damage_statmod,
    make_remove_statmod,
    make_statmod_appearance,
    validate_statmod,
    validate_appear,
)
from ..registry import register_bot

BOT_ID = "blackout_cin_tf"


@register_bot(BOT_ID, name_zh="眩晕", desc="霸天虎空中巨无霸，爆破系重装饱和轰炸专家")
def build_blackout_abilities(base_hp: float = 40519.0, base_atk: float = 3272.0):
    mods = {}
    appears = {}
    buffs = {}

    # =========================================================================
    # 1. [ID: 1794966881655] 被动 - 连击暴击几率 (Crit Rate)
    #    连击数每增加5，获得1层12%的暴击几率增益，被敌人命中打断连击时全部移除
    # =========================================================================
    appr_combo_crit_rate = make_statmod_appearance(
        appr_id="appr_blackout_combo_crit_rate",
        callout_text="暴击几率",
        desc="连击数每增加5，暴击几率提升12%，连招被打断时移除",
        pua_icon="\uE40D",
        color=AbilityColor.ORANGE_DAMAGE,
        show_callout=True,
    )
    mod_combo_crit_rate = {
        "id": "blackout_combo_crit_rate",
        "t": "crit_rate",
        "tm": "",
        "tr": [],
        "uit": [],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.12,
        "d": -1.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 99,
        "g": "crit_rate",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_blackout_combo_crit_rate"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_appear(appr_combo_crit_rate)
    validate_statmod(mod_combo_crit_rate)
    appears[appr_combo_crit_rate["id"]] = appr_combo_crit_rate
    mods[mod_combo_crit_rate["id"]] = mod_combo_crit_rate

    m_rem_crit_rate, _ = make_remove_statmod(
        mod_id="blackout_crit_rate_remove_on_hit",
        target_mod_id="blackout_combo_crit_rate",
        trigger="",
        trigger_scope="",
        show_callout=False,
    )
    mods.update(m_rem_crit_rate)

    # =========================================================================
    # 2. [ID: 1794966881657] 被动 - 无尽怒火 (Infinite Fury)
    #    当暴击率超过100%时，溢出的每1%转化为1%暴伤增益，低于100%时移除
    # =========================================================================
    appr_infinite_fury = make_statmod_appearance(
        appr_id="appr_blackout_infinite_fury",
        callout_text="无尽怒火",
        desc="暴击率溢出100%部分转化为等额暴击伤害增益",
        pua_icon="\uE906",
        color=AbilityColor.ORANGE_DAMAGE,
        show_callout=True,
    )
    mod_infinite_fury = {
        "id": "blackout_infinite_fury_crit_dmg",
        "t": "crit_damage",
        "tm": "",
        "tr": [],
        "uit": [],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.0,
        "d": -1.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "infinite_fury",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_blackout_infinite_fury"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_appear(appr_infinite_fury)
    validate_statmod(mod_infinite_fury)
    appears[appr_infinite_fury["id"]] = appr_infinite_fury
    mods[mod_infinite_fury["id"]] = mod_infinite_fury

    m_rem_fury, _ = make_remove_statmod(
        mod_id="blackout_fury_remove_on_hit",
        target_mod_id="blackout_infinite_fury_crit_dmg",
        trigger="",
        trigger_scope="",
        show_callout=False,
    )
    mods.update(m_rem_fury)

    # =========================================================================
    # 4. [ID: 1794966881659] 被动 - 重击暴击燃烧 (Heavy Attack Burn)
    #    重击如果暴击，100%造成持续6秒相当于80%攻击力的燃烧伤害
    # =========================================================================
    m_heavy_burn, a_heavy_burn = make_burn_statmod(
        mod_id="blackout_heavy_crit_burn",
        duration=6.0,
        total_dmg=float(round(base_atk * 0.80)),
        chance=1.0,
        trigger="onCrit",
        trigger_scope="level=Heavy",
        appr_id="appr_blackout_heavy_burn",
        callout_text="导弹灼烧",
        pua_icon="\uE41D",
        color_hex=AbilityColor.RED_DEBUFF_TC,
        gradient_bottom=AbilityColor.RED_DEBUFF_GB,
    )
    mods.update(m_heavy_burn)
    appears.update(a_heavy_burn)

    # =========================================================================
    # 5. [ID: 1794966881664] 特殊技 1 (能量炮) - 不可防御 (Unblockable)
    #    最后1击不可防御 // 最后一击的时间内出现浅紫色图标 (C4BBF8 / 7E22CE)
    #    破防效果由 move_blackout_special_01 (hd.u=True) 与本修饰器双重保障，
    #    图标起止时间窗由 skill_blackout.c 精准控制。
    # =========================================================================
    appr_sp1_unblockable = make_statmod_appearance(
        appr_id="appr_blackout_sp1_unblockable",
        callout_text="不可防御",
        desc="能量炮最后一击不可防御，强行穿透对手格挡",
        pua_icon="\uE41F",
        color=AbilityColor.LIGHT_PURPLE_POWER,
        show_callout=True,
    )
    mod_sp1_unblockable = {
        "id": "blackout_sp1_unblockable",
        "t": "unblockable",
        "tm": "",
        "tr": [],
        "uit": [],
        "pri": 1,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 1.0,
        "d": 3.5,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "unblockable",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_blackout_sp1_unblockable"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_appear(appr_sp1_unblockable)
    validate_statmod(mod_sp1_unblockable)
    appears[appr_sp1_unblockable["id"]] = appr_sp1_unblockable
    mods[mod_sp1_unblockable["id"]] = mod_sp1_unblockable

    # =========================================================================
    # 6. [ID: 1794966881668] 特殊技 1 (能量炮) - 特殊伤害 (Special Damage)
    #    技能期间提升30%的特殊伤害 (SP1 激活挂载，SP1 退出由 skill_blackout.c 立即移除)
    # =========================================================================
    m_sp1_spec_dmg, a_sp1_spec_dmg = make_attack_boost_statmod(
        mod_id="blackout_sp1_special_damage",
        duration=3.5,
        attack_bonus=0.30,
        chance=1.0,
        trigger="onSpecial1Activate",
        trigger_scope="",
        appr_id="appr_blackout_sp1_special_dmg",
        callout_text="特殊伤害",
        pua_icon="\uE41C",
        color_hex=AbilityColor.ORANGE_DAMAGE_TC,
        gradient_bottom=AbilityColor.ORANGE_DAMAGE_GB,
    )
    mods.update(m_sp1_spec_dmg)
    appears.update(a_sp1_spec_dmg)

    # =========================================================================
    # 7. [ID: 1794966881662 & 1794966881663] 特殊技 2 (翼刃回旋) - 暴击伤害与可叠加暴击流血
    #    a) 技能期间提升60%暴击伤害 (SP2 结束立即由 skill_blackout.c 移除)
    #    b) 每1击暴击100%概率触发3秒流血，可叠加 (60%攻击力伤害)
    # =========================================================================
    m_sp2_crit_dmg, a_sp2_crit_dmg = make_crit_damage_statmod(
        mod_id="blackout_sp2_crit_damage",
        duration=4.0,
        crit_dmg_bonus=0.60,
        chance=1.0,
        trigger="onSpecial2Activate",
        trigger_scope="",
        appr_id="appr_blackout_sp2_crit_dmg",
        callout_text="暴击强化",
        pua_icon="\uE906",
        color_hex=AbilityColor.ORANGE_DAMAGE_TC,
        gradient_bottom=AbilityColor.ORANGE_DAMAGE_GB,
    )
    mods.update(m_sp2_crit_dmg)
    appears.update(a_sp2_crit_dmg)

    m_sp2_bleed, a_sp2_bleed = make_bleed_statmod(
        mod_id="blackout_sp2_crit_bleed",
        duration=3.0,
        total_dmg=float(round(base_atk * 0.60)),
        chance=1.0,
        trigger="onCrit",
        trigger_scope="level=Special2",
        stackable=True,
        appr_id="appr_blackout_sp2_bleed",
        callout_text="撕裂流血",
        pua_icon="\uE401",
        color_hex=AbilityColor.RED_DEBUFF_TC,
        gradient_bottom=AbilityColor.RED_DEBUFF_GB,
    )
    # 显式放开最大叠层上限至 99，确保多段暴击全部独立叠加
    m_sp2_bleed["blackout_sp2_crit_bleed"]["st"] = 99
    mods.update(m_sp2_bleed)
    appears.update(a_sp2_bleed)

    # =========================================================================
    # 8. [ID: 1794966881660 & 1794966881661] 特殊技 3 (猎杀) - 暴击燃烧与可叠加永久暴抗减益
    #    a) 最后一击暴击率+50%
    #    b) 最后一击暴击造成持续6秒80%攻击力燃烧伤害
    #    c) 最后一击命中向对手施加1层永久暴击抗性减益 (对手受暴击率提升20%，可叠加)
    # =========================================================================
    m_sp3_crit_rate, a_sp3_crit_rate = make_crit_rate_statmod(
        mod_id="blackout_sp3_last_crit_rate",
        duration=2.0,
        crit_bonus=0.50,
        chance=1.0,
        trigger="",
        trigger_scope="",
        appr_id="appr_blackout_sp3_crit_rate",
        callout_text="锁定暴击",
        pua_icon="\uE40D",
        color_hex=AbilityColor.ORANGE_DAMAGE_TC,
        gradient_bottom=AbilityColor.ORANGE_DAMAGE_GB,
    )
    mods.update(m_sp3_crit_rate)
    appears.update(a_sp3_crit_rate)

    m_sp3_burn, a_sp3_burn = make_burn_statmod(
        mod_id="blackout_sp3_crit_burn",
        duration=6.0,
        total_dmg=float(round(base_atk * 0.80)),
        chance=1.0,
        trigger="",
        trigger_scope="",
        appr_id="appr_blackout_sp3_burn",
        callout_text="地毯焚烧",
        pua_icon="\uE41D",
        color_hex=AbilityColor.RED_DEBUFF_TC,
        gradient_bottom=AbilityColor.RED_DEBUFF_GB,
    )
    mods.update(m_sp3_burn)
    appears.update(a_sp3_burn)

    appr_sp3_crit_resist = make_statmod_appearance(
        appr_id="appr_blackout_crit_resist_debuff",
        callout_text="暴击抗性减益",
        desc="对手暴击抗性永久降低20%，受暴击几率提升（可叠加）",
        pua_icon="\uE409",
        color=AbilityColor.RED_DEBUFF,
        show_callout=True,
    )
    mod_sp3_crit_resist = {
        "id": "blackout_sp3_crit_resist_debuff",
        "t": "crit_rate",
        "tm": "",
        "tr": [],
        "uit": [],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.20,
        "d": -1.0,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 99,
        "g": "crit_resist_debuff_sp3",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_blackout_crit_resist_debuff"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_appear(appr_sp3_crit_resist)
    validate_statmod(mod_sp3_crit_resist)
    appears[appr_sp3_crit_resist["id"]] = appr_sp3_crit_resist
    mods[mod_sp3_crit_resist["id"]] = mod_sp3_crit_resist

    # =========================================================================
    # 9. [ID: 1794966881665] 觉醒能力 - 追猎 (I'll Hunt You Down!)
    #    普通攻击（近战/远程/重击）落空时，获得 1 层 60% 能量功率增益，持续 3 秒；
    #    最大 1 层，再次触发时刷新倒计时。
    # =========================================================================
    appr_sig_power = make_statmod_appearance(
        appr_id="appr_blackout_sig_power",
        callout_text="能量功率",
        desc="普通攻击落空获得60%能量功率增益持续3秒，再次触发刷新倒计时",
        pua_icon="\uE608",
        color=AbilityColor.LIGHT_PURPLE_POWER,
        show_callout=True,
    )
    mod_sig_power = {
        "id": "blackout_sig_whiff_power_gain",
        "t": "power_rate",
        "tm": "",
        "tr": [],
        "uit": [],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.60,
        "d": 3.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "power_rate_buff",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_blackout_sig_power"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_appear(appr_sig_power)
    validate_statmod(mod_sig_power)
    appears[appr_sig_power["id"]] = appr_sig_power
    mods[mod_sig_power["id"]] = mod_sig_power

    # 消除静默移除修饰器的未注册外观告警
    for m in mods.values():
        if m.get("t") == "remove":
            m["a"] = []

    return mods, appears, buffs
