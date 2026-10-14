#!/usr/bin/env python3
"""
Bot Ability Implementation: 天火 (Jetfire)
=========================================
Bot ID: jetfire_gs_leader2014
阵营: 汽车人 (Autobot) | 职业: 科技系 (Tech)

【官方技能真理源对照 (来自 Upstash KV 实时端点与 TFTF 数据库)】：
-----------------------------------------------------------------------------
1. [被动 - 招架护盾] (ID: 2656, pua_icon: 0xe911)
   - 在最接近状态下对普通远程攻击和远程重击进行格挡会激活招架护盾，
     将该远程攻击以100%的原始攻击力反弹回去。
   - 在最接近状态下对普通近战攻击进行格挡会激活招架护盾，
     本次格挡不产生防御伤害，并且对手会眩晕1秒。
   - 连续射击特性：敌人连开三枪时，招架一次可以反弹这全部三枪 (持续反弹护盾窗口)。
   - 护盾视觉：出护盾的时候有一个专门的光圈与 HUD 提示。
2. [被动 - 能量充能] (ID: 2657, pua_icon: 0xe914)
   - 每次成功招架，获得一个能量充能，最多10层 (紫色图标，无倒计时)。
   - 每层能量充能提升能量功率(Power Rate) 5% (满层10层提升50%)。
-----------------------------------------------------------------------------
"""

from ..core import (
    make_shock_statmod,
    validate_color_code,
    validate_statmod,
)
from ..registry import register_bot

BOT_ID = "jetfire_gs_leader2014"


@register_bot(BOT_ID, name_zh="天火", desc="经典G1科技系飞行领袖，完美招架开启反弹护盾，近战招架完全免伤击晕对手，招架积蓄能量充能持续提升能量功率")
def build_jetfire_abilities(base_hp: float = 28975.0, base_atk: float = 2260.0):
    mods = {}
    appears = {}

    # -------------------------------------------------------------------------
    # 1. 被动 - 招架护盾 (ID: 2656): Parry Shield
    # -------------------------------------------------------------------------
    validate_color_code("38BDF8", "parry_shield_tc")
    validate_color_code("0284C7", "parry_shield_gb")
    appr_shield = {
        "id": "appr_jetfire_parry_shield",
        "a": "招架护盾",
        "s": "招架护盾",
        "l": "最接近状态格挡激活护盾，100%反弹远程攻击与重击；近战完全免伤并眩晕对手1秒",
        "ss": "招架护盾",
        "t": "\uE911",
        "f": "",
        "st": "招架护盾",
        "ps": "招架护盾",
        "pl": "招架护盾生效中",
        "tc": "38BDF8",
        "gt": "38BDF8",
        "gb": "0284C7",
    }
    mod_shield = {
        "id": "jetfire_parry_shield",
        "t": "protection",
        "tm": "",
        "tr": ["always"],
        "uit": ["always"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 1.0,
        "d": 0.0,
        "s": "none",
        "ta": "self",
        "mt": "passive",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "parry_shield",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_jetfire_parry_shield"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_shield)
    mods["jetfire_parry_shield"] = mod_shield
    appears["appr_jetfire_parry_shield"] = appr_shield

    # -------------------------------------------------------------------------
    # 2. 被动 - 能量充能 (ID: 2657): Energy Charge
    # -------------------------------------------------------------------------
    validate_color_code("A855F7", "energy_charge_tc")
    validate_color_code("7E22CE", "energy_charge_gb")
    appr_charge = {
        "id": "appr_jetfire_energy_charge",
        "a": "能量充能",
        "s": "能量充能",
        "l": "成功招架获得1层能量充能(上限10层)，每层提升能量功率5%",
        "ss": "能量充能",
        "t": "\uE914",
        "f": "",
        "st": "能量充能",
        "ps": "能量充能",
        "pl": "能量充能生效中",
        "tc": "A855F7",
        "gt": "A855F7",
        "gb": "7E22CE",
    }
    mod_charge = {
        "id": "jetfire_energy_charge",
        "t": "power",
        "tm": "",
        "tr": ["manual"],
        "uit": ["manual"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 1.0,
        "d": -1.0,  # 负数持续时间表示永久/无倒计时堆叠buff (IsIndefinite=true)
        "s": "none",
        "ta": "self",
        "mt": "buff",  # buff类型以便在BuffsController中维护层数与UI显示
        "v": "",
        "ms": "",
        "st": 10,  # 最多 10 层
        "g": "energy_charge",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_jetfire_energy_charge"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_charge)
    mods["jetfire_energy_charge"] = mod_charge
    appears["appr_jetfire_energy_charge"] = appr_charge

    # -------------------------------------------------------------------------
    # 3. 被动 - 震击 (ID: 2658): Shock on Heavy Attack Hit
    # -------------------------------------------------------------------------
    # 重击命中时，消耗一个能量充能，给对手施加一层震击，造成攻击力90%的伤害，持续4秒。
    m_shock, a_shock = make_shock_statmod(
        mod_id="jetfire_heavy_shock",
        duration=4.0,
        total_dmg=float(round(base_atk * 0.90)),
        chance=1.0,
        trigger="manual",
        appr_id="appr_jetfire_heavy_shock",
        callout_text="震击",
        show_callout=True,
        pua_icon="\uE914",
        stackable=True,
        target_actor="opponent",
    )
    mods.update(m_shock)
    appears.update(a_shock)

    return mods, appears
