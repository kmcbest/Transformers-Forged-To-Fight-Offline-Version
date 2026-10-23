#!/usr/bin/env python3
"""
Bot Ability Implementation: 黑暗擎天柱 / 暗天陨 (Nemesis Prime)
==============================================================
Bot ID: nemesisprime_gs_voyager2015
阵营: 霸天虎 (Decepticon) | 职业: 战术系 (Tactician)

【官方技能真理源对照 (来自 Upstash KV 聚合 Priorities 清单)】：
-----------------------------------------------------------------------------
1. [被动 - 暗能量] (ID: 3209, pua_icon: 0xe90a)
   - 暗天陨血量在50~100%时每10秒获得一个黑暗能量充能，15~50%时每7秒获得一个，低于15%时每5秒获得一个，最多获得10层。
   - 开局显现紫色 (#D204F6) 倒计时图标 (\uE407)，倒计时走完获得紫色 (\uE90A) 层数图标，满10层后倒计时图标消失，少于10层时恢复倒计时。
2. [被动 - 重击驱散] (ID: 3218, pua_icon: 0xe950)
   - 重击命中时驱散一个近战或护甲增益。每有一个黑暗能量充能，重击伤害+5%。
3. [觉醒 - 赝品领导模块] (ID: 3221, pua_icon: 0xe503)
   - 将特殊技造成伤害的25%转化为生命值 (吸血)。
4. [SP3 - 不可防御] (ID: 3224, pua_icon: 0xe41f)
   - 技能结束后，暗天陨的普通攻击全部不可防御，持续7秒，每有一个黑暗能量充能，持续时间增加0.5秒。消耗全部黑暗能量充能。
-----------------------------------------------------------------------------
"""

from ..core import (
    AbilityColor,
    make_statmod_appearance,
    make_heal_statmod,
    validate_color_code,
    validate_statmod,
)
from ..registry import register_bot

BOT_ID = "nemesisprime_gs_voyager2015"


@register_bot(BOT_ID, name_zh="暗天陨", desc="战术系堕落领袖，黑暗能量周期涌动，重击驱散增益并增伤，赝品领导模块特技吸血，SP3全普攻不可防御")
def build_nemesisprime_abilities(base_hp: float = 31500.0, base_atk: float = 2380.0):
    mods = {}
    appears = {}

    # 1a. 黑暗能量充能倒计时: 开局即显现深紫色 \uE407 倒计时图标 (10s / 7s / 5s)
    appr_dark_cd = make_statmod_appearance(
        appr_id="appr_nemesisprime_dark_cd",
        desc="随血量每10秒/7秒/5秒充能一层黑暗能量",
        short_desc="黑暗能量充能倒计时",
        pua_icon="\uE407",
        color=AbilityColor.DARK_PURPLE_SPECIAL,
        show_callout=False,
        active_desc="黑暗能量充能中",
    )
    mod_dark_cd = {
        "id": "nemesisprime_dark_cd",
        "t": "attack_buff",
        "tm": "",
        "tr": ["onStart"],
        "uit": ["onStart"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.0,
        "d": 10.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "dark_energy_cd",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_nemesisprime_dark_cd"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_dark_cd)
    mods["nemesisprime_dark_cd"] = mod_dark_cd
    appears["appr_nemesisprime_dark_cd"] = appr_dark_cd

    # 1b. 黑暗能量层数 (ID: 3209): 深紫色 \uE90A 图标，无倒计时 (d=-1.0)，上限 10 层
    appr_dark = make_statmod_appearance(
        appr_id="appr_nemesisprime_dark_energy",
        callout_text="黑暗能量",
        desc="血量越低充能越快(上限10层)，每层提升重击伤害5%",
        short_desc="黑暗能量充能",
        pua_icon="\uE90A",
        color=AbilityColor.DARK_PURPLE_SPECIAL,
        show_callout=True,
        active_desc="黑暗能量生效中",
    )
    mod_dark = {
        "id": "nemesisprime_dark_energy",
        "t": "attack_buff",
        "tm": "",
        "tr": ["onStart"],
        "uit": ["onStart"],
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
        "st": 10,
        "g": "dark_energy",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_nemesisprime_dark_energy"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_dark)
    mods["nemesisprime_dark_energy"] = mod_dark
    appears["appr_nemesisprime_dark_energy"] = appr_dark

    # 2. 重击驱散 (ID: 3218): 重击命中驱散近战/护甲增益
    appr_dispel = make_statmod_appearance(
        appr_id="appr_nemesisprime_heavy_dispel",
        callout_text="重击驱散",
        desc="重击驱散目标一个近战或护甲增益",
        short_desc="重击增益驱散",
        pua_icon="\uE950",
        color=AbilityColor.RED_DEBUFF,
        show_callout=True,
        active_desc="重击驱散生效中",
    )
    mod_dispel = {
        "id": "nemesisprime_heavy_dispel",
        "t": "passive",
        "tm": "",
        "tr": ["onHit"],
        "uit": ["onHit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "level=Heavy",
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
        "g": "dispel",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_nemesisprime_heavy_dispel"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_dispel)
    mods["nemesisprime_heavy_dispel"] = mod_dispel
    appears["appr_nemesisprime_heavy_dispel"] = appr_dispel

    # 3. 觉醒赝品领导模块 (ID: 3221, pua_icon: 0xe503):
    # a) 特殊技激活时显现 6 秒生命汲取增益 (血条下方显现 E503 倒计时圆环图标与呼出条)
    appr_mat_buff = make_statmod_appearance(
        appr_id="appr_nemesisprime_matrix_buff",
        callout_text="赝品领导模块",
        desc="特殊技造成伤害的25%转化为生命值",
        short_desc="特技吸血25%",
        pua_icon="\uE503",
        color=AbilityColor.GREEN_HEALTH,
        show_callout=True,
        active_desc="生命汲取生效中",
    )
    mod_mat_buff = {
        "id": "nemesisprime_matrix_buff",
        "t": "buff",
        "tm": "",
        "tr": ["onSpecialActivate"],
        "uit": ["onSpecialActivate"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 1.0,
        "d": 6.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "lifesteal",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_nemesisprime_matrix_buff"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_mat_buff)
    mods["nemesisprime_matrix_buff"] = mod_mat_buff
    appears["appr_nemesisprime_matrix_buff"] = appr_mat_buff

    # b) 特殊技命中即时回血与跳绿字 (与救护车对齐，接入底层 Heal_BuffEffect，每击回复 25% ATK)
    matrix_heal_amount = float(round(base_atk * 0.25, 2))
    m_matrix, a_matrix = make_heal_statmod(
        mod_id="nemesisprime_matrix_lifesteal",
        duration=0.0,
        heal_amount=matrix_heal_amount,
        chance=1.0,
        trigger="onSpecialHit",
        trigger_scope="",
        buff_id="heal",
        appr_id="appr_nemesisprime_matrix_lifesteal",
        callout_text="生命汲取",
        pua_icon="\uE503",
        show_callout=True,
    )
    mods.update(m_matrix)
    appears.update(a_matrix)

    # 4. SP3 不可防御 (ID: 3224): 基础攻击不可防御 7s (+0.5s/层)
    appr_unbl = make_statmod_appearance(
        appr_id="appr_nemesisprime_sp3_unblockable",
        callout_text="绝对破防",
        desc="技能结束后基础攻击全部不可防御，持续7秒以上",
        short_desc="全攻击破防",
        pua_icon="\uE41F",
        color=AbilityColor.ORANGE_DAMAGE,
        show_callout=True,
        active_desc="绝对破防生效中",
    )
    mod_unbl = {
        "id": "nemesisprime_sp3_unblockable",
        "t": "buff",
        "tm": "",
        "tr": ["onSpecial3Expiry"],
        "uit": ["onSpecial3Expiry"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 1.0,
        "d": 7.0,
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
        "a": ["appr_nemesisprime_sp3_unblockable"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_unbl)
    mods["nemesisprime_sp3_unblockable"] = mod_unbl
    appears["appr_nemesisprime_sp3_unblockable"] = appr_unbl

    return mods, appears
