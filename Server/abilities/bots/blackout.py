#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bot Ability Implementation: 眩晕 (Blackout)
===========================================
Bot ID: blackout_cin_tf
阵营: 霸天虎 (Decepticon) | 职业: 破坏分子 (Demolitions / demo)
基准数值: HP 40519, ATK 3272
"""

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from ..core import (
    make_armor_up_statmod,
    make_burn_statmod,
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

    # 1. 被动 - 强化复合装甲 (Armor Buff): 受击 12% 概率减伤 38%, 持续 6s
    m_armor, a_armor = make_armor_up_statmod(
        mod_id="blackout_passive_armor",
        duration=6.0,
        armor_bonus=0.38,
        chance=0.12,
        trigger="onPreDamage",
        trigger_scope="",
        appr_id="appr_blackout_armor",
        callout_text="装甲强化",
        show_callout=True,
        pua_icon="\uE517",
        color_hex="7097B7",
        gradient_bottom="2E4C6D",
        stackable=True,
        max_stacks=3,
    )
    mods.update(m_armor)
    appears.update(a_armor)

    # 2. 特殊技 1 (震荡波S1) - 电磁震荡炮 (EMP Shock Blast): 最后一击 100% 削减能量与电磁减益
    appr_emp = {
        "id": "appr_blackout_emp_shock",
        "a": "电磁过载",
        "s": "",
        "l": "电磁脉冲压制，能量流失中",
        "ss": "电磁过载",
        "t": "\uE41D",
        "f": "",
        "st": "电磁过载",
        "ps": "电磁过载",
        "pl": "电磁过载中",
        "tc": "00DDFF",
        "gt": "00DDFF",
        "gb": "0055AA",
    }
    statmod_emp = {
        "id": "blackout_sp1_emp_shock",
        "t": "direct_damage",
        "tm": "",
        "tr": ["onSpecial1Hit"],
        "uit": ["onSpecial1Hit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.35,
        "d": 0.0,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_blackout_emp_shock"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(statmod_emp)
    validate_appear(appr_emp)
    mods["blackout_sp1_emp_shock"] = statmod_emp
    appears["appr_blackout_emp_shock"] = appr_emp

    # 3. 特殊技 2 (碾碎器原版S2) - 旋翼导弹齐射 (Rotor Missile Barrage): 100% 施加持续燃烧 DOT
    m_burn, a_burn = make_burn_statmod(
        mod_id="blackout_sp2_burn",
        duration=6.0,
        total_dmg=base_atk * 1.20,
        chance=1.0,
        trigger="onSpecial2Hit",
        trigger_scope="",
        appr_id="appr_blackout_burn",
        callout_text="导弹灼烧",
        pua_icon="\uE41D",
        color_hex="FF4400",
        gradient_bottom="881100",
        stackable=True,
        max_stacks=3,
    )
    mods.update(m_burn)
    appears.update(a_burn)

    # 4. 特殊技 3 (地毯轰炸) - 战术封锁与暴击削弱
    appr_lockdown = {
        "id": "appr_blackout_sp3_lockdown",
        "a": "战术压制",
        "s": "",
        "l": "战术地毯轰炸，封锁特殊技并削弱暴击",
        "ss": "战术压制",
        "t": "\uE419",
        "f": "",
        "st": "战术压制",
        "ps": "战术压制",
        "pl": "战术压制中",
        "tc": "CC0000",
        "gt": "CC0000",
        "gb": "660000",
    }
    statmod_lockdown = {
        "id": "blackout_sp3_lockdown",
        "t": "crit_rate_debuff",
        "tm": "",
        "tr": ["onSpecial3Hit"],
        "uit": ["onSpecial3Hit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": -0.50,
        "d": 10.0,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_blackout_sp3_lockdown"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(statmod_lockdown)
    validate_appear(appr_lockdown)
    mods["blackout_sp3_lockdown"] = statmod_lockdown
    appears["appr_blackout_sp3_lockdown"] = appr_lockdown

    return mods, appears, buffs
