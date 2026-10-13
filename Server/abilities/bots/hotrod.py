#!/usr/bin/env python3
"""
Bot Ability Implementation: 热破 (Hot Rod)
=========================================
Bot ID: hotrod_cin_tlk
阵营: 汽车人 (Autobot) | 职业: 战士系 (Warrior)

【官方技能真理源对照 (来自 Upstash KV 聚合 Priorities 清单)】：
-----------------------------------------------------------------------------
1. [被动 - 眩晕] (ID: 2550, pua_icon: 0xe605)
   - 致命重击：重击暴击触发眩晕 2.5 秒。
2. [被动 - 能量功率减益] (ID: 2562, pua_icon: 0xe606)
   - 减速中的对方无法规避；每层减速降低对手能量功率 27.2%。
3. [SP2 - 减速] (ID: 2563, pua_icon: 0xe952)
   - 远程攻击命中或被防御时，有60%的概率施加减速，持续3.2秒。
4. [SP3 - 减速] (ID: 2564, pua_icon: 0xe952)
   - 远程攻击命中或被防御时，有60%的概率施加减速，持续3.2秒。
-----------------------------------------------------------------------------
"""

from ..core import (
    make_stun_statmod,
    validate_color_code,
    validate_statmod,
)
from ..registry import register_bot

BOT_ID = "hotrod_cin_tlk"


@register_bot(BOT_ID, name_zh="热破", desc="战士系时间停滞者，致命重击暴击眩晕，时空减速绝对封锁闪避并压制能量功率")
def build_hotrod_abilities(base_hp: float = 29500.0, base_atk: float = 2420.0):
    mods = {}
    appears = {}

    # 1. 致命重击眩晕 (ID: 2550): 重击暴击触发 2.5 秒眩晕
    m_stun, a_stun = make_stun_statmod(
        mod_id="hotrod_heavy_stun",
        duration=2.5,
        chance=1.0,
        trigger="onCrit",
        trigger_scope="level=Heavy",
        appr_id="appr_hotrod_heavy_stun",
        callout_text="眩晕",
        pua_icon="\uE605",
    )
    mods.update(m_stun)
    appears.update(a_stun)

    # 2. 能量功率减益 / 禁规避 (ID: 2562): 减速中对手无法规避，能量功率 -27.2%
    validate_color_code("3B82F6", "hotrod_pwr_tc")
    validate_color_code("1D4ED8", "hotrod_pwr_gb")
    appr_pwr = {
        "id": "appr_hotrod_decel_power_rate_debuff",
        "a": "时间停滞",
        "s": "功率削减",
        "l": "减速目标无法闪避规避，能量获取功率降低27.2%",
        "ss": "时空封锁",
        "t": "\uE606",
        "f": "",
        "st": "减速封锁",
        "ps": "时间停滞",
        "pl": "时间停滞生效中",
        "tc": "3B82F6",
        "gt": "3B82F6",
        "gb": "1D4ED8",
    }
    mod_pwr = {
        "id": "hotrod_decel_power_rate_debuff",
        "t": "passive",
        "tm": "",
        "tr": ["always"],
        "uit": ["always"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.272,
        "d": 0.0,
        "s": "none",
        "ta": "self",
        "mt": "passive",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "deceleration_suppress",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_hotrod_decel_power_rate_debuff"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_pwr)
    mods["hotrod_decel_power_rate_debuff"] = mod_pwr
    appears["appr_hotrod_decel_power_rate_debuff"] = appr_pwr

    # 3. SP2 减速 (ID: 2563): 远程 60% 施加 3.2 秒减速
    validate_color_code("06B6D4", "decel_tc")
    validate_color_code("0891B2", "decel_gb")
    appr_decel = {
        "id": "appr_hotrod_sp2_deceleration",
        "a": "减速",
        "s": "减速",
        "l": "使目标陷入时空减速，无法规避闪避，持续3.2秒",
        "ss": "时空减速",
        "t": "\uE952",
        "f": "",
        "st": "减速",
        "ps": "减速",
        "pl": "减速生效中",
        "tc": "06B6D4",
        "gt": "06B6D4",
        "gb": "0891B2",
    }
    mod_decel2 = {
        "id": "hotrod_sp2_deceleration",
        "t": "debuff",
        "tm": "",
        "tr": ["onHit"],
        "uit": ["onHit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "level=Special2",
        "trr": "repeat",
        "c": 0.60,
        "m": 1.0,
        "d": 3.2,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "deceleration",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_hotrod_sp2_deceleration"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_decel2)
    mods["hotrod_sp2_deceleration"] = mod_decel2
    appears["appr_hotrod_sp2_deceleration"] = appr_decel

    # 4. SP3 减速 (ID: 2564): 远程 60% 施加 3.2 秒减速
    mod_decel3 = {
        "id": "hotrod_sp3_deceleration",
        "t": "debuff",
        "tm": "",
        "tr": ["onSpecial3Activate"],
        "uit": ["onSpecial3Activate"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 0.60,
        "m": 1.0,
        "d": 3.2,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "deceleration",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_hotrod_sp2_deceleration"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_decel3)
    mods["hotrod_sp3_deceleration"] = mod_decel3

    return mods, appears
