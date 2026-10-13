#!/usr/bin/env python3
"""
Bot Ability Implementation: 巨蝎勇士 (Scorponok)
===============================================
Bot ID: scorponok_bw_kabam
阵营: 原始兽 (Predacon) | 职业: 战士系 (Warrior)

【官方技能真理源对照 (来自 Upstash KV 聚合 Priorities 清单)】：
-----------------------------------------------------------------------------
1. [被动 - 毒液充能] (ID: 3253, pua_icon: 0xe40a)
   - 充满一格能量时，获得一层毒液充能，无倒计时，可叠加，每层充能增加20%的攻击力。//橙色图标
2. [SP1 - 目眩] (ID: 3264, pua_icon: 0xe519)
   - 技能命中时施加目眩，敌人的基础远程攻击有60%的概率无法命中，特殊远程攻击100%无法命中，持续9.5秒。
3. [被动 - 毒液逆火] (ID: 3276, pua_icon: 0xe901)
   - 重击命中，将所有毒液充能转化为对应层数的逆火减益，持续12秒。
     对手在逆火减益状态下使用特殊技，将被施加与逆火相同层数的瞬间震击，每层造成攻击力153%的伤害。
4. [SP2 - 毒液逆火] (ID: 3277, pua_icon: 0xe901)
   - 技能结束时，将所有毒液充能转化为对应层数的逆火减益，持续12秒。
     对手在逆火减益状态下使用特殊技，将被施加与逆火相同层数的瞬间震击，每层造成攻击力153%的伤害。
5. [SP3 - 目眩] (ID: 3278, pua_icon: 0xe519)
   - 技能命中时施加目眩，敌人的基础远程攻击有60%的概率无法命中，特殊远程攻击100%无法命中，持续26秒。
-----------------------------------------------------------------------------
"""

from ..core import (
    make_bleed_statmod,
    make_attack_boost_statmod,
    validate_color_code,
    validate_statmod,
)
from ..registry import register_bot

BOT_ID = "scorponok_bw_kabam"


@register_bot(BOT_ID, name_zh="巨蝎勇士", desc="战士系剧毒刺客，能量积蓄毒液充能，重击与SP2逆火反噬必杀技，生化目眩封杀远程")
def build_scorponok_abilities(base_hp: float = 30000.0, base_atk: float = 2350.0):
    mods = {}
    appears = {}

    # 1. 毒液充能 (ID: 3253): 满 1 格能量获 1 层 (+20% 攻击力，橙色图标，无倒计时)
    validate_color_code("F97316", "venom_charge_tc")
    validate_color_code("C2410C", "venom_charge_gb")
    appr_charge = {
        "id": "appr_scorponok_venom_charge",
        "a": "毒液充能",
        "s": "毒液充能",
        "l": "每充盈一格能量获得一层充能，每层提升20%攻击力",
        "ss": "毒液攻击提升",
        "t": "\uE40A",
        "f": "",
        "st": "毒液充能",
        "ps": "毒液充能",
        "pl": "毒液充能生效中",
        "tc": "F97316",
        "gt": "F97316",
        "gb": "C2410C",
    }
    mod_charge = {
        "id": "scorponok_venom_charge",
        "t": "attack_buff",
        "tm": "",
        "tr": ["always"],
        "uit": ["always"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.20,
        "d": 0.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 3,
        "g": "venom_charge",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_scorponok_venom_charge"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_charge)
    mods["scorponok_venom_charge"] = mod_charge
    appears["appr_scorponok_venom_charge"] = appr_charge

    # 2. SP1 目眩 (ID: 3264): 命中施加 9.5 秒目眩 (远程攻击失准)
    validate_color_code("3B82F6", "daze_tc")
    validate_color_code("1D4ED8", "daze_gb")
    appr_daze1 = {
        "id": "appr_scorponok_sp1_daze",
        "a": "目眩",
        "s": "目眩",
        "l": "基础远程攻击60%无法命中，特技远程100%无法命中",
        "ss": "远程射击失准",
        "t": "\uE519",
        "f": "",
        "st": "目眩",
        "ps": "目眩",
        "pl": "目眩生效中",
        "tc": "3B82F6",
        "gt": "3B82F6",
        "gb": "1D4ED8",
    }
    mod_daze1 = {
        "id": "scorponok_sp1_daze",
        "t": "debuff",
        "tm": "",
        "tr": ["onSpecial1Activate"],
        "uit": ["onSpecial1Activate"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.60,
        "d": 9.5,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "daze",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_scorponok_sp1_daze"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_daze1)
    mods["scorponok_sp1_daze"] = mod_daze1
    appears["appr_scorponok_sp1_daze"] = appr_daze1

    # 3. 被动毒液逆火 (ID: 3276): 重击将充能转逆火 12 秒
    validate_color_code("EF4444", "backfire_tc")
    validate_color_code("B91C1C", "backfire_gb")
    appr_bf = {
        "id": "appr_scorponok_venom_backfire",
        "a": "逆火",
        "s": "逆火",
        "l": "对手使用特殊技时，受到逆火反噬震击伤害",
        "ss": "必杀技反噬震击",
        "t": "\uE901",
        "f": "",
        "st": "逆火",
        "ps": "逆火",
        "pl": "逆火生效中",
        "tc": "EF4444",
        "gt": "EF4444",
        "gb": "B91C1C",
    }
    mod_bf_p = {
        "id": "scorponok_venom_backfire_passive",
        "t": "debuff",
        "tm": "",
        "tr": ["onHit"],
        "uit": ["onHit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "level=Heavy",
        "trr": "repeat",
        "c": 1.0,
        "m": 1.53,
        "d": 12.0,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 3,
        "g": "backfire",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_scorponok_venom_backfire"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_bf_p)
    mods["scorponok_venom_backfire_passive"] = mod_bf_p
    appears["appr_scorponok_venom_backfire"] = appr_bf

    # 4. SP2 毒液逆火 (ID: 3277): SP2 结束将充能转逆火 12 秒
    mod_bf_sp2 = {
        "id": "scorponok_venom_backfire_sp2",
        "t": "debuff",
        "tm": "",
        "tr": ["onSpecial2Expiry"],
        "uit": ["onSpecial2Expiry"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 1.53,
        "d": 12.0,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 3,
        "g": "backfire",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_scorponok_venom_backfire"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_bf_sp2)
    mods["scorponok_venom_backfire_sp2"] = mod_bf_sp2

    # 5. SP3 目眩 (ID: 3278): 命中施加 26 秒目眩
    appr_daze3 = {
        "id": "appr_scorponok_sp3_daze",
        "a": "超长目眩",
        "s": "超长目眩",
        "l": "基础远程攻击60%无法命中，特技远程100%无法命中(持续26秒)",
        "ss": "远程射击失准",
        "t": "\uE519",
        "f": "",
        "st": "目眩",
        "ps": "目眩",
        "pl": "目眩生效中",
        "tc": "3B82F6",
        "gt": "3B82F6",
        "gb": "1D4ED8",
    }
    mod_daze3 = {
        "id": "scorponok_sp3_daze",
        "t": "debuff",
        "tm": "",
        "tr": ["onSpecial3Activate"],
        "uit": ["onSpecial3Activate"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.60,
        "d": 26.0,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "daze",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_scorponok_sp3_daze"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_daze3)
    mods["scorponok_sp3_daze"] = mod_daze3
    appears["appr_scorponok_sp3_daze"] = appr_daze3

# 6. [既有技能保留] 近战暴击流血 (ID: 3275): 40% 几率施加 4.0 秒流血 (60% ATK)
    m_bleed, a_bleed = make_bleed_statmod(
        mod_id="scorponok_melee_crit_bleed",
        duration=4.0,
        total_dmg=float(round(base_atk * 0.60)),
        chance=0.40,
        trigger="onCrit",
        trigger_scope="level=Light,Medium,Heavy",
        appr_id="appr_scorponok_bleed",
        callout_text="流血",
        buff_id="dmg_bleed",
    )
    mods.update(m_bleed)
    appears.update(a_bleed)

    return mods, appears

