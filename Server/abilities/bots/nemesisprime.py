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
    make_armor_break_statmod,
    make_statmod_appearance,
    validate_appear,
    validate_statmod,
)
from ..registry import register_bot

BOT_ID = "nemesisprime_gs_voyager2015"


@register_bot(BOT_ID, name_zh="暗天陨", desc="战术系堕落领袖，黑暗能量周期涌动与脉冲克隆，重击/SP2驱散，SP1复刻减益，赝品领导模块特技吸血，SP3全普攻不可防御")
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
        "t": "nemesis_dark_cd",
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
        "t": "nemesis_dark_energy",
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

    # 1c. 被动 - 亚空间脉冲克隆体 (ID: 3217): 复制对手近战或护甲增益 (25% + 5%/层)
    appr_cloner = make_statmod_appearance(
        appr_id="appr_nemesisprime_subspace_cloner",
        callout_text="亚空间脉冲克隆",
        desc="对手获得近战增益或护甲增益时，有概率复制同强度同时长增益至自身",
        short_desc="克隆近战/护甲增益",
        pua_icon="\uE90A",
        color=AbilityColor.DARK_PURPLE_SPECIAL,
        show_callout=True,
        active_desc="亚空间克隆成功",
    )
    mod_cloner = {
        "id": "nemesisprime_subspace_cloner",
        "t": "combat",
        "tm": "",
        "tr": [],
        "uit": [],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.0,
        "d": 1.5,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "subspace_cloner",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_nemesisprime_subspace_cloner"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_appear(appr_cloner)
    validate_statmod(mod_cloner)
    mods["nemesisprime_subspace_cloner"] = mod_cloner
    appears["appr_nemesisprime_subspace_cloner"] = appr_cloner

    # 2. 重击驱散 (ID: 3218): 重击命中随机驱散近战/护甲增益 (仅实际驱散成功时呼出)
    appr_dispel = make_statmod_appearance(
        appr_id="appr_nemesisprime_heavy_dispel",
        callout_text="重击驱散",
        desc="重击随机驱散目标一个近战或护甲增益",
        short_desc="重击增益驱散",
        pua_icon="\uE950",
        color=AbilityColor.RED_DEBUFF,
        show_callout=True,
        active_desc="重击驱散生效中",
    )
    mod_dispel = {
        "id": "nemesisprime_heavy_dispel",
        "t": "combat",
        "tm": "",
        "tr": [],
        "uit": [],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.0,
        "d": 1.0,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
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
    # 由 skill_nemesis.c 在每段特殊技命中时按实际伤害 25% 调用 skill_heal 精准回血并闪现绿字 503
    appr_matrix = make_statmod_appearance(
        appr_id="appr_nemesisprime_matrix_lifesteal",
        callout_text="赝品领导模块",
        desc="将特殊技实际造成伤害的25%转化为生命值",
        short_desc="特技吸血25%",
        pua_icon="\uE503",
        color=AbilityColor.GREEN_HEALTH,
        show_callout=True,
        active_desc="赝品领导模块回血",
    )
    mod_matrix = {
        "id": "nemesisprime_matrix_lifesteal",
        "t": "combat",
        "tm": "",
        "tr": [],
        "uit": [],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.0,
        "d": 1.2,
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
        "a": ["appr_nemesisprime_matrix_lifesteal"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_appear(appr_matrix)
    validate_statmod(mod_matrix)
    mods["nemesisprime_matrix_lifesteal"] = mod_matrix
    appears["appr_nemesisprime_matrix_lifesteal"] = appr_matrix

    # 4. SP1 黑暗能量斩: 末击复制自身全部减益至对手 (30%+3%/层, 原强度原时间) + 结束获2层充能
    appr_sp1_clone = make_statmod_appearance(
        appr_id="appr_nemesisprime_sp1_clone_debuff",
        callout_text="黑暗能量斩",
        desc="把暗天陨身上的全部减益按原强度与原时间复制到对手身上",
        short_desc="减益转移复刻",
        pua_icon="\uE90A",
        color=AbilityColor.DARK_PURPLE_SPECIAL,
        show_callout=True,
        active_desc="黑暗能量斩复刻",
    )
    mod_sp1_clone = {
        "id": "nemesisprime_sp1_clone_debuff",
        "t": "combat",
        "tm": "",
        "tr": [],
        "uit": [],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.0,
        "d": 1.5,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "dark_clone_debuff",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_nemesisprime_sp1_clone_debuff"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_appear(appr_sp1_clone)
    validate_statmod(mod_sp1_clone)
    mods["nemesisprime_sp1_clone_debuff"] = mod_sp1_clone
    appears["appr_nemesisprime_sp1_clone_debuff"] = appr_sp1_clone

    # 5. SP2 邪恶之斧: 驱散近战增益 -> 5% 近战减益(4s); 驱散护甲增益 -> 5% 破甲(4s)
    appr_sp2_melee_debuff = make_statmod_appearance(
        appr_id="appr_nemesisprime_sp2_melee_debuff",
        callout_text="近战减益",
        desc="近战攻击伤害降低 5%（可叠加），持续 4 秒",
        short_desc="近战减益5%",
        pua_icon="\uE950",
        color=AbilityColor.RED_DEBUFF,
        show_callout=True,
        active_desc="近战减益生效中",
    )
    mod_sp2_melee_debuff = {
        "id": "nemesisprime_sp2_melee_debuff",
        "t": "attack_debuff",
        "tm": "",
        "tr": [],
        "uit": [],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.05,
        "d": 4.0,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 10,
        "g": "melee_debuff",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_nemesisprime_sp2_melee_debuff"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_appear(appr_sp2_melee_debuff)
    validate_statmod(mod_sp2_melee_debuff)
    mods["nemesisprime_sp2_melee_debuff"] = mod_sp2_melee_debuff
    appears["appr_nemesisprime_sp2_melee_debuff"] = appr_sp2_melee_debuff

    m_sp2_ab, a_sp2_ab = make_armor_break_statmod(
        mod_id="nemesisprime_sp2_armor_break",
        duration=4.0,
        break_amount=0.05,
        chance=1.0,
        trigger="",
        trigger_scope="",
        appr_id="appr_nemesisprime_sp2_armor_break",
        callout_text="破甲",
        pua_icon="\uE516",
        stackable=True,
        max_stacks=10,
    )
    mods.update(m_sp2_ab)
    appears.update(a_sp2_ab)

    # 6. SP3 不可防御 (ID: 3224): 技能结束后基础攻击全部不可防御 7s (+0.5s/层), 消耗全部黑暗能量
    appr_unbl = make_statmod_appearance(
        appr_id="appr_nemesisprime_sp3_unblockable",
        callout_text="不可防御",
        desc="技能结束后基础攻击全部不可防御，持续7秒以上",
        short_desc="不可防御",
        pua_icon="\uE41F",
        color=AbilityColor.LIGHT_PURPLE_POWER,
        show_callout=True,
        active_desc="不可防御生效中",
    )
    mod_unbl = {
        "id": "nemesisprime_sp3_unblockable",
        "t": "unblockable",
        "tm": "",
        "tr": [],
        "uit": [],
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
