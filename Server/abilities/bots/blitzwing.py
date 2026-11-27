#!/usr/bin/env python3
"""
Bot Ability Implementation: 闪电 (Blitzwing)
===========================================
Bot ID: blitzwing_gs
阵营: 霸天虎 (Decepticon) | 职业: 战术系 (Tactician)

【官方技能真理源对照 (来自 character_abilities 数据库)】：
-----------------------------------------------------------------------------
1. [觉醒能力 - 三变金刚 / Triple Changer]
   - 官方描述: 未觉醒前，战斗开始时随机锁定一种形态进行战斗，觉醒后按住防御1秒，可切换变形形态，并使用对应的重击和特殊技。
   - 实现方案: 开局默认坦克形态，按住防御1.0秒切换为战机形态，再次按住防御1.0秒切换回坦克形态。

2. [基础能力 - 坦克模式 / Tank Mode]
   - 官方描述: 坦克模式提升火力与装甲。
   - 实现方案: 赋予 blitzwing_tank_mode，图标 \\uE902。

3. [基础能力 - 飞机模式 / Jet Mode]
   - 官方描述: 飞机模式提升精准和生存能力。
   - 实现方案: 赋予 blitzwing_jet_mode，图标 \\uE184。

4. [被动能力 - 护甲增益 / Armor Buff]
   - 官方描述: 当进入坦克模式时，有 50% 的概率获得 1 层护甲增益，降低受到攻击伤害的 20%，持续 5 秒。
   - 实现方案: 触发时赋予 blitzwing_tank_armor，提升护甲 20%，持续 5.0 秒。

5. [被动能力 - 暴击几率 / Crit Rate]
   - 官方描述: 进入飞机模式时，有 50% 的概率获得 1 层 30% 的暴击几率增益，持续 7 秒。
   - 实现方案: 触发时赋予 blitzwing_jet_crit，提升暴击率 30%，持续 7.0 秒。

6. [核心战术 - 抑制夹钳 / Inhibitor Clamp]
   - 官方描述:
     - L4 或 M2 命中对手时，有 20% 的概率施加 1 层抑制夹钳，持续 4 秒，可叠加。
     - 重击命中对手时，有 80% 的概率施加 1 层抑制夹钳，持续 4 秒，可叠加。
     - 如果处于坦克模式，抑制夹钳将抵消对方下一次要获得的增益（图标为红色，对方侧弹出“增益阻塞”红字）。
     - 如果处于飞机模式，抑制夹钳将抵消对方下一次要施加的减益（图标为红色，对方侧弹出“减益阻塞”红字）。
   - 实现方案:
     - 坦克模式夹钳: blitzwing_clamp_tank (红色 \\uE98A)
     - 战机模式夹钳: blitzwing_clamp_jet (红色 \\uE98A)
     - SP3 通用永久夹钳: blitzwing_clamp_sp3 (白色 \\uE98A)

7. [被动能力 - 绝处逢生 / Second Wind]
   - 官方描述:
     生命力降至 25% 时：
     - 如果处于坦克模式，获得 1 层 75% 的护甲增益，持续 8 秒；
     - 如果处于飞机模式，获得 1 层 75% 的特殊伤害增益，持续 8 秒；
     - 如果对手身上有抑制夹钳，则全数引爆，造成 2.5 秒的眩晕。
   - 实现方案:
     - 坦克极限护甲: blitzwing_sw_armor (75% 护甲, 8.0 秒)
     - 战机极限特殊增益: blitzwing_sw_special (75% 特殊增益, 8.0 秒)
     - 引爆所有夹钳并调用 skill_stun_player 造成 2.5 秒强控眩晕。
-----------------------------------------------------------------------------
"""

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from ..core import (
    AbilityColor,
    make_statmod_appearance,
    validate_statmod,
)
from ..registry import register_bot

BOT_ID = "blitzwing_gs"


@register_bot(BOT_ID, name_zh="闪电", desc="霸天虎战术系三变战士，长按防御1秒切换坦克形态(重击放炮)与战机形态(重击冲撞)，独门抑制夹钳战术控制")
def build_blitzwing_abilities(base_hp: float = 38250.0, base_atk: float = 2795.0):
    mods = {}
    appears = {}
    buffs = {}

    # -------------------------------------------------------------------------
    # 1. 固有形态标记 (Stance Modes)
    # -------------------------------------------------------------------------
    appr_tank = make_statmod_appearance(
        appr_id="appr_blitzwing_tank_mode",
        callout_text="坦克形态",
        desc="闪电处于坦克形态，重击变形为坦克炮击，强化装甲与火力",
        short_desc="坦克形态",
        pua_icon="\uE902",
        color=AbilityColor.WHITE_SPECIAL,
        show_callout=True,
        active_desc="坦克形态",
    )
    mods["blitzwing_tank_mode"] = {
        "id": "blitzwing_tank_mode", "t": "attack_buff", "tm": "", "tr": ["onStart"],
        "uit": ["onStart"], "pri": 0, "trm": 0.0, "trs": "", "trr": "repeat",
        "c": 1.0, "m": 0.0, "d": -1.0, "s": "none", "ta": "self", "mt": "buff",
        "v": "", "ms": "", "st": 1, "g": "blitzwing_stance", "gc": 0.0, "gcv": "",
        "rcv": "", "ti": 0, "a": ["appr_blitzwing_tank_mode"], "au": [], "rh": 0.0, "ra": 0.0,
    }
    appears["appr_blitzwing_tank_mode"] = appr_tank

    appr_jet = make_statmod_appearance(
        appr_id="appr_blitzwing_jet_mode",
        callout_text="战机形态",
        desc="闪电处于战机形态，重击变形为战机冲撞，强化精准与机动",
        short_desc="战机形态",
        pua_icon="\uE184",
        color=AbilityColor.WHITE_SPECIAL,
        show_callout=True,
        active_desc="战机形态",
    )
    mods["blitzwing_jet_mode"] = {
        "id": "blitzwing_jet_mode", "t": "attack_buff", "tm": "", "tr": [],
        "uit": [], "pri": 0, "trm": 0.0, "trs": "", "trr": "repeat",
        "c": 1.0, "m": 0.0, "d": -1.0, "s": "none", "ta": "self", "mt": "buff",
        "v": "", "ms": "", "st": 1, "g": "blitzwing_stance", "gc": 0.0, "gcv": "",
        "rcv": "", "ti": 0, "a": ["appr_blitzwing_jet_mode"], "au": [], "rh": 0.0, "ra": 0.0,
    }
    appears["appr_blitzwing_jet_mode"] = appr_jet

    # -------------------------------------------------------------------------
    # 2. 抑制夹钳核心 Debuff (Inhibitor Clamps)
    # -------------------------------------------------------------------------
    # 2.1 坦克形态夹钳 (抵消增益, 红色 \uE923)
    appr_clamp_tank = make_statmod_appearance(
        appr_id="appr_blitzwing_clamp_tank",
        callout_text="抑制夹钳",
        desc="受抑制夹钳约束：下一次要获得的增益将被抵消消除",
        short_desc="抑制夹钳",
        pua_icon="\uE923",
        color=AbilityColor.RED_DEBUFF,
        show_callout=True,
    )
    mods["blitzwing_clamp_tank"] = {
        "id": "blitzwing_clamp_tank", "t": "combat", "tm": "", "tr": [],
        "uit": [], "pri": 0, "trm": 0.0, "trs": "", "trr": "repeat",
        "c": 1.0, "m": 0.0, "d": 4.0, "s": "none", "ta": "opponent", "mt": "debuff",
        "v": "", "ms": "", "st": 10, "g": "blitzwing_clamp", "gc": 0.0, "gcv": "",
        "rcv": "", "ti": 0, "a": ["appr_blitzwing_clamp_tank"], "au": [], "rh": 0.0, "ra": 0.0,
    }
    appears["appr_blitzwing_clamp_tank"] = appr_clamp_tank

    # 2.2 战机形态夹钳 (抵消减益, 红色 \uE923)
    appr_clamp_jet = make_statmod_appearance(
        appr_id="appr_blitzwing_clamp_jet",
        callout_text="抑制夹钳",
        desc="受抑制夹钳约束：下一次施加的所有减益将被抵消消除",
        short_desc="抑制夹钳",
        pua_icon="\uE923",
        color=AbilityColor.RED_DEBUFF,
        show_callout=True,
    )
    mods["blitzwing_clamp_jet"] = {
        "id": "blitzwing_clamp_jet", "t": "combat", "tm": "", "tr": [],
        "uit": [], "pri": 0, "trm": 0.0, "trs": "", "trr": "repeat",
        "c": 1.0, "m": 0.0, "d": 4.0, "s": "none", "ta": "opponent", "mt": "debuff",
        "v": "", "ms": "", "st": 10, "g": "blitzwing_clamp", "gc": 0.0, "gcv": "",
        "rcv": "", "ti": 0, "a": ["appr_blitzwing_clamp_jet"], "au": [], "rh": 0.0, "ra": 0.0,
    }
    appears["appr_blitzwing_clamp_jet"] = appr_clamp_jet

    # 2.3 SP3 通用永久夹钳 (双重阻塞, 白色 \uE923)
    appr_clamp_sp3 = make_statmod_appearance(
        appr_id="appr_blitzwing_clamp_sp3",
        callout_text="抑制夹钳",
        desc="受永久抑制夹钳强力约束：抵消下一次要获得的正向增益或施加的负面减益",
        short_desc="抑制夹钳",
        pua_icon="\uE923",
        color=AbilityColor.WHITE_SPECIAL,
        show_callout=True,
    )
    mods["blitzwing_clamp_sp3"] = {
        "id": "blitzwing_clamp_sp3", "t": "combat", "tm": "", "tr": [],
        "uit": [], "pri": 0, "trm": 0.0, "trs": "", "trr": "repeat",
        "c": 1.0, "m": 0.0, "d": -1.0, "s": "none", "ta": "opponent", "mt": "debuff",
        "v": "", "ms": "", "st": 5, "g": "blitzwing_clamp_sp3", "gc": 0.0, "gcv": "",
        "rcv": "", "ti": 0, "a": ["appr_blitzwing_clamp_sp3"], "au": [], "rh": 0.0, "ra": 0.0,
    }
    appears["appr_blitzwing_clamp_sp3"] = appr_clamp_sp3

    # -------------------------------------------------------------------------
    # 3. 伴生被动与 SP 增益/减益
    # -------------------------------------------------------------------------
    # 3.1 坦克形态 20% 护甲增益 (5s, 蓝色 \uE517)
    appr_tank_armor = make_statmod_appearance(
        appr_id="appr_blitzwing_tank_armor", callout_text="护甲增益",
        desc="坦克模式护甲强化：受到攻击伤害降低 20%", short_desc="护甲增益",
        pua_icon="\uE517", color=AbilityColor.BLUE_DEFENSE, show_callout=True,
    )
    mods["blitzwing_tank_armor"] = {
        "id": "blitzwing_tank_armor", "t": "armor_up", "tm": "", "tr": [], "uit": [],
        "pri": 0, "trm": 0.0, "trs": "", "trr": "repeat", "c": 1.0, "m": 0.20, "d": 5.0,
        "s": "none", "ta": "self", "mt": "buff", "v": "", "ms": "", "st": 1,
        "g": "armor_up", "gc": 0.0, "gcv": "", "rcv": "", "ti": 0, "a": ["appr_blitzwing_tank_armor"],
        "au": [], "rh": 0.0, "ra": 0.0,
    }
    appears["appr_blitzwing_tank_armor"] = appr_tank_armor

    # 3.2 飞机形态 30% 暴击率增益 (7s, 黄色 \uE40D)
    appr_jet_crit = make_statmod_appearance(
        appr_id="appr_blitzwing_jet_crit", callout_text="暴击几率",
        desc="飞机模式精准锁定：暴击率提升 30%", short_desc="暴击几率",
        pua_icon="\uE40D", color=AbilityColor.YELLOW_STATUS, show_callout=True,
    )
    mods["blitzwing_jet_crit"] = {
        "id": "blitzwing_jet_crit", "t": "crit_rate", "tm": "", "tr": [], "uit": [],
        "pri": 0, "trm": 0.0, "trs": "", "trr": "repeat", "c": 1.0, "m": 0.30, "d": 7.0,
        "s": "none", "ta": "self", "mt": "buff", "v": "", "ms": "", "st": 1,
        "g": "crit_rate", "gc": 0.0, "gcv": "", "rcv": "", "ti": 0, "a": ["appr_blitzwing_jet_crit"],
        "au": [], "rh": 0.0, "ra": 0.0,
    }
    appears["appr_blitzwing_jet_crit"] = appr_jet_crit

    # 3.3 SP1 战机破甲 (7s, 30%, 蓝色 \uE516)
    appr_sp1_armor_break = make_statmod_appearance(
        appr_id="appr_blitzwing_sp1_armor_break", callout_text="破甲",
        desc="SP1战机破甲：削减目标 30% 护甲评级", short_desc="破甲",
        pua_icon="\uE516", color=AbilityColor.BLUE_DEFENSE, show_callout=True,
    )
    mods["blitzwing_sp1_armor_break"] = {
        "id": "blitzwing_sp1_armor_break", "t": "armor_break", "tm": "", "tr": [], "uit": [],
        "pri": 0, "trm": 0.0, "trs": "", "trr": "repeat", "c": 1.0, "m": 0.30, "d": 7.0,
        "s": "Armor", "ta": "opponent", "mt": "debuff", "v": "", "ms": "", "st": 1,
        "g": "", "gc": 0.0, "gcv": "", "rcv": "", "ti": 0, "a": ["appr_blitzwing_sp1_armor_break"],
        "au": [], "rh": 0.0, "ra": 0.0,
    }
    appears["appr_blitzwing_sp1_armor_break"] = appr_sp1_armor_break

    # 3.4 SP1 坦克攻击减益 (7s, 30%, 红色 \uE916)
    appr_sp1_attack_debuff = make_statmod_appearance(
        appr_id="appr_blitzwing_sp1_attack_debuff", callout_text="攻击减益",
        desc="SP1坦克重炮压制：降低对手 30% 攻击力", short_desc="攻击减益",
        pua_icon="\uE916", color=AbilityColor.RED_DEBUFF, show_callout=True,
    )
    mods["blitzwing_sp1_attack_debuff"] = {
        "id": "blitzwing_sp1_attack_debuff", "t": "attack_debuff", "tm": "", "tr": [], "uit": [],
        "pri": 0, "trm": 0.0, "trs": "", "trr": "repeat", "c": 1.0, "m": 0.30, "d": 7.0,
        "s": "Attack", "ta": "opponent", "mt": "debuff", "v": "", "ms": "", "st": 1,
        "g": "", "gc": 0.0, "gcv": "", "rcv": "", "ti": 0, "a": ["appr_blitzwing_sp1_attack_debuff"],
        "au": [], "rh": 0.0, "ra": 0.0,
    }
    appears["appr_blitzwing_sp1_attack_debuff"] = appr_sp1_attack_debuff

    # 3.5 SP2 坦克攻击增益 (7s, 30%, 橙色 \uE406)
    appr_sp2_attack_buff = make_statmod_appearance(
        appr_id="appr_blitzwing_sp2_attack_buff", callout_text="攻击增益",
        desc="SP2坦克重炮突袭：提升自身 30% 攻击力", short_desc="攻击增益",
        pua_icon="\uE406", color=AbilityColor.ORANGE_DAMAGE, show_callout=True,
    )
    mods["blitzwing_sp2_attack_buff"] = {
        "id": "blitzwing_sp2_attack_buff", "t": "attack_buff", "tm": "", "tr": [], "uit": [],
        "pri": 0, "trm": 0.0, "trs": "", "trr": "repeat", "c": 1.0, "m": 0.30, "d": 7.0,
        "s": "Attack", "ta": "self", "mt": "buff", "v": "", "ms": "", "st": 1,
        "g": "", "gc": 0.0, "gcv": "", "rcv": "", "ti": 0, "a": ["appr_blitzwing_sp2_attack_buff"],
        "au": [], "rh": 0.0, "ra": 0.0,
    }
    appears["appr_blitzwing_sp2_attack_buff"] = appr_sp2_attack_buff

    # 3.6 绝处逢生：75% 护甲 (8s, \uE517) / 75% 特殊伤害 (8s, \uE41C)
    appr_sw_armor = make_statmod_appearance(
        appr_id="appr_blitzwing_sw_armor", callout_text="绝处逢生",
        desc="绝处逢生：重型装甲展开，受到伤害降低 75%", short_desc="绝处逢生",
        pua_icon="\uE517", color=AbilityColor.BLUE_DEFENSE, show_callout=True,
    )
    mods["blitzwing_sw_armor"] = {
        "id": "blitzwing_sw_armor", "t": "armor_up", "tm": "", "tr": [], "uit": [],
        "pri": 0, "trm": 0.0, "trs": "", "trr": "repeat", "c": 1.0, "m": 0.75, "d": 8.0,
        "s": "none", "ta": "self", "mt": "buff", "v": "", "ms": "", "st": 1,
        "g": "armor_up", "gc": 0.0, "gcv": "", "rcv": "", "ti": 0, "a": ["appr_blitzwing_sw_armor"],
        "au": [], "rh": 0.0, "ra": 0.0,
    }
    appears["appr_blitzwing_sw_armor"] = appr_sw_armor

    appr_sw_special = make_statmod_appearance(
        appr_id="appr_blitzwing_sw_special", callout_text="绝处逢生",
        desc="绝处逢生：超载巡航，特殊攻击伤害提升 75%", short_desc="绝处逢生",
        pua_icon="\uE41C", color=AbilityColor.ORANGE_DAMAGE, show_callout=True,
    )
    mods["blitzwing_sw_special"] = {
        "id": "blitzwing_sw_special", "t": "special_damage_buff", "tm": "", "tr": [], "uit": [],
        "pri": 0, "trm": 0.0, "trs": "", "trr": "repeat", "c": 1.0, "m": 0.75, "d": 8.0,
        "s": "Attack", "ta": "self", "mt": "buff", "v": "", "ms": "", "st": 1,
        "g": "", "gc": 0.0, "gcv": "", "rcv": "", "ti": 0, "a": ["appr_blitzwing_sw_special"],
        "au": [], "rh": 0.0, "ra": 0.0,
    }
    appears["appr_blitzwing_sw_special"] = appr_sw_special

    for m in mods.values():
        validate_statmod(m)

    return mods, appears, buffs
