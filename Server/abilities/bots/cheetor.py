#!/usr/bin/env python3
"""
Bot Ability Implementation: 黄豹 (Cheetor)
===========================================
Bot ID: cheetor_bw_transmetal
阵营: 巨无霸 (Maximal) | 职业: 侦察兵 (Scout)

【官方技能真理源对照 (来自 character_abilities 数据库)】：
-----------------------------------------------------------------------------
1. [被动 - 能量守护 / Power Guard] (ID: 2453)
   - 官方描述: "黄豹对吸取能量的技能（能量流失、能量燃烧）免疫，此类技能无法扣减黄豹的能量"
   - 实现方案:
     cheetor_power_guard: Native C 检测并阻止能量扣减。

2. [被动 - 暴击流血 / Crit Bleed] (ID: 2457)
   - 官方描述: "近战攻击出暴击时，有45%的概率触发流血，造成攻击力65%的伤害，持续4秒。"
   - 实现方案:
     cheetor_crit_bleed: 触发 onCrit，造成 65% ATK 4.0 秒流血。

3. [被动 - 能量获取 / Combo Power Gain] (ID: 2455)
   - 官方描述: "L4或者M2命中对手的时候，在1秒内获得最大能量槽的2.5%"
   - 实现方案:
     cheetor_combo_power_gain: 触发 onHit，限制 level=Light4,Medium2，获得 2.5% 最大能量 (7.5 点 Mana)。

4. [被动 - 重击规避远程 / Heavy Evade Ranged] (ID: 2460)
   - 官方描述: "黄豹重击过程中有35%的概率穿透对方的基础远程和远程重击，如果没有触发穿透，则100%的概率触发规避"
   - 实现方案:
     cheetor_heavy_evade_ranged: Native C 结合穿透与规避逻辑。

5. [觉醒技 - 野生突击 / Feral Strike] (ID: 2461)
   - 官方描述: "每充满一格能量，黄豹得到4秒的野生突击状态（黄色图标），在此增益过程中：
     1. 所有攻击暴击率增加40%
     2. 所有攻击无视对方护甲
     3. 对手无法规避（对手侧显示一个红色的E92A图标）
     4. 对手无法触发任何技能（无法得到增益，也无法施加减益）
     5. 黄豹自己有25%的概率规避近战攻击"
   - 实现方案:
     cheetor_signature_feral_strike: 满格触发 4 秒全能压制状态。

6. [特殊技1 - 阻止修复与流血 / SP1] (ID: 2462, 2463)
   - 官方描述:
     a) 施加阻止修复，禁用对方所有回血能力，直到对方流血状态解除。
     b) 最后一击命中时100%概率触发流血，施加攻击力100%的伤害，持续8秒。
   - 实现方案:
     cheetor_sp1_heal_block, cheetor_sp1_bleed。

7. [特殊技2 - 伤害放大与能量功率 / SP2] (ID: 2463)
   - 官方描述:
     a) 对手能量越少，该攻击伤害越大，最大造成50%的额外伤害。
     b) 获得能量功率增益，能量获取量增加50%，持续12秒。
   - 实现方案:
     cheetor_sp2_dmg_amp, cheetor_sp2_power_buff。

8. [特殊技3 - 伤害放大、能量锁定与能量燃烧 / SP3] (ID: 2464)
   - 官方描述:
     a) 对手能量越少，该攻击伤害越大，最大造成100%的额外伤害。
     b) 技能完成时100%概率触发能量锁定，阻止对方获得能量，持续10秒。
     c) 0.5秒内扣减对方最大能量的3%。
   - 实现方案:
     cheetor_sp3_dmg_amp, cheetor_sp3_power_lock, cheetor_sp3_power_burn。
-----------------------------------------------------------------------------
"""

from ..core import (
    AbilityColor,
    make_bleed_statmod,
    make_statmod_appearance,
    make_condition_scope,
    validate_statmod,
    validate_appear,
    validate_color_code,
)
from ..registry import register_bot

BOT_ID = "cheetor_bw_transmetal"


@register_bot(BOT_ID, name_zh="黄豹", desc="侦察兵，能量免疫守护、暴击流血、连击充能、重击穿透规避、满气野生突击、SP禁疗与残气伤害放大")
def build_cheetor_abilities(base_hp: float = 28245.0, base_atk: float = 2874.0):
    """
    根据基准属性生成黄豹专属全套能力修饰器。
    基准 5星50级 HP = 28245.0, ATK = 2874.0
    """
    mods = {}
    appears = {}
    buffs = {}

    # -------------------------------------------------------------------------
    # 1. 暴击流血 4.0s (65% ATK, 45% 概率) (ID: 2457)
    # -------------------------------------------------------------------------
    bleed_dmg = float(round(base_atk * 0.65, 2))
    m_bleed, a_bleed = make_bleed_statmod(
        mod_id="cheetor_crit_bleed",
        duration=4.0,
        total_dmg=bleed_dmg,
        chance=0.45,
        trigger="onCrit",
        trigger_scope="level=Light,Medium,Heavy",
        appr_id="appr_cheetor_crit_bleed",
        callout_text="流血",
        stackable=True,
    )
    mods.update(m_bleed)
    appears.update(a_bleed)

    # -------------------------------------------------------------------------
    # 2. L4 与 M2 命中连击能量获取 2.5% (7.5 点 Mana) (ID: 2455)
    # -------------------------------------------------------------------------
    appr_combo_power = make_statmod_appearance(
        appr_id="appr_cheetor_combo_power_gain",
        callout_text="能量获取",
        desc="连击完成时获得2.5%最大能量",
        pua_icon="\uE608",
        color=AbilityColor.LIGHT_PURPLE_POWER,
        show_callout=True,
    )
    mod_combo_power = {
        "id": "cheetor_combo_power_gain",
        "t": "power_gain",
        "tm": "",
        "tr": ["onHit"],
        "uit": ["onHit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "level=Light4,Medium2",
        "trr": "repeat",
        "c": 1.0,
        "m": 7.5,
        "d": 1.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "power_gain_buff",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_cheetor_combo_power_gain"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_combo_power)
    validate_appear(appr_combo_power)
    mods["cheetor_combo_power_gain"] = mod_combo_power
    appears["appr_cheetor_combo_power_gain"] = appr_combo_power

    # -------------------------------------------------------------------------
    # 3. 觉醒技：野生突击 (Feral Strike) 4.0s (ID: 2461)
    # 黄色图标，暴击率 +40%，破甲，近战规避 25%
    # -------------------------------------------------------------------------
    appr_feral = make_statmod_appearance(
        appr_id="appr_cheetor_signature_feral_strike",
        callout_text="野生突击",
        desc="获得4秒野生突击：暴击率增加40%，无视护甲，对手无法规避或触发技能，自身25%规避近战",
        pua_icon="\uE160",
        color=AbilityColor.YELLOW_STATUS,
        show_callout=True,
    )
    mod_feral = {
        "id": "cheetor_signature_feral_strike",
        "t": "crit_rate",
        "tm": "",
        "tr": ["onHit"],
        "uit": ["onHit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.40,
        "d": 4.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "feral_buff",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_cheetor_signature_feral_strike"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_feral)
    validate_appear(appr_feral)
    mods["cheetor_signature_feral_strike"] = mod_feral
    appears["appr_cheetor_signature_feral_strike"] = appr_feral

    # 对手无法规避标记 (红色 E92A)
    appr_feral_opp = make_statmod_appearance(
        appr_id="appr_cheetor_feral_no_evade",
        callout_text="无法规避",
        desc="在黄豹野生突击期间无法进行闪避或规避",
        pua_icon="\uE92A",
        color=AbilityColor.RED_DEBUFF,
        show_callout=True,
    )
    mod_feral_opp = {
        "id": "cheetor_feral_no_evade",
        "t": "decel",
        "tm": "",
        "tr": ["onHit"],
        "uit": ["onHit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 1.0,
        "d": 4.0,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "no_evade_debuff",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_cheetor_feral_no_evade"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_feral_opp)
    validate_appear(appr_feral_opp)
    mods["cheetor_feral_no_evade"] = mod_feral_opp
    appears["appr_cheetor_feral_no_evade"] = appr_feral_opp

    # -------------------------------------------------------------------------
    # 4. SP1：阻止修复 (Heal Block) (ID: 2462)
    # -------------------------------------------------------------------------
    appr_heal_block = make_statmod_appearance(
        appr_id="appr_cheetor_sp1_heal_block",
        callout_text="禁疗",
        desc="禁用对手所有生命回复能力，直到流血状态解除",
        pua_icon="\uE90C",
        color=AbilityColor.RED_DEBUFF,
        show_callout=True,
    )
    mod_heal_block = {
        "id": "cheetor_sp1_heal_block",
        "t": "heal_block",
        "tm": "",
        "tr": ["onHit"],
        "uit": ["onHit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "level=Special1",
        "trr": "repeat",
        "c": 1.0,
        "m": 1.0,
        "d": 8.0,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "heal_block_debuff",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_cheetor_sp1_heal_block"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_heal_block)
    validate_appear(appr_heal_block)
    mods["cheetor_sp1_heal_block"] = mod_heal_block
    appears["appr_cheetor_sp1_heal_block"] = appr_heal_block

    # -------------------------------------------------------------------------
    # 5. SP1：收招流血 8.0s (100% ATK) (ID: 2463)
    # -------------------------------------------------------------------------
    sp1_bleed_dmg = float(round(base_atk * 1.00, 2))
    m_sp1_bleed, a_sp1_bleed = make_bleed_statmod(
        mod_id="cheetor_sp1_bleed",
        duration=8.0,
        total_dmg=sp1_bleed_dmg,
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Special1",
        appr_id="appr_cheetor_sp1_bleed",
        callout_text="流血",
        stackable=True,
    )
    mods.update(m_sp1_bleed)
    appears.update(a_sp1_bleed)

    # -------------------------------------------------------------------------
    # 6. SP2：能量功率增益 +50% 持续 12 秒 (ID: 2463)
    # -------------------------------------------------------------------------
    appr_sp2_power = make_statmod_appearance(
        appr_id="appr_cheetor_sp2_power_buff",
        callout_text="能量功率",
        desc="能量获取量增加50%，持续12秒",
        pua_icon="\uE608",
        color=AbilityColor.LIGHT_PURPLE_POWER,
        show_callout=True,
    )
    mod_sp2_power = {
        "id": "cheetor_sp2_power_buff",
        "t": "power_rate",
        "tm": "",
        "tr": ["onHit"],
        "uit": ["onHit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "level=Special2",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.50,
        "d": 12.0,
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
        "a": ["appr_cheetor_sp2_power_buff"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_sp2_power)
    validate_appear(appr_sp2_power)
    mods["cheetor_sp2_power_buff"] = mod_sp2_power
    appears["appr_cheetor_sp2_power_buff"] = appr_sp2_power

    # -------------------------------------------------------------------------
    # 7. SP3：能量锁定 10 秒 (ID: 2464)
    # -------------------------------------------------------------------------
    appr_sp3_lock = make_statmod_appearance(
        appr_id="appr_cheetor_sp3_power_lock",
        callout_text="能量锁定",
        desc="封锁对手能量槽，使其无法获得能量，持续10秒",
        pua_icon="\uE523",
        color=AbilityColor.RED_DEBUFF,
        show_callout=True,
    )
    mod_sp3_lock = {
        "id": "cheetor_sp3_power_lock",
        "t": "power_lock",
        "tm": "",
        "tr": ["onHit"],
        "uit": ["onHit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "level=Special3",
        "trr": "repeat",
        "c": 1.0,
        "m": 1.0,
        "d": 10.0,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "power_lock_debuff",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_cheetor_sp3_power_lock"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_sp3_lock)
    validate_appear(appr_sp3_lock)
    mods["cheetor_sp3_power_lock"] = mod_sp3_lock
    appears["appr_cheetor_sp3_power_lock"] = appr_sp3_lock

    # -------------------------------------------------------------------------
    # 8. SP3：能量燃烧 3% (9 点 Mana) (ID: 2464)
    # -------------------------------------------------------------------------
    appr_sp3_burn = make_statmod_appearance(
        appr_id="appr_cheetor_sp3_power_burn",
        callout_text="能量燃烧",
        desc="瞬间燃烧扣除对手3%最大能量",
        pua_icon="\uE607",
        color=AbilityColor.RED_DEBUFF,
        show_callout=True,
    )
    mod_sp3_burn = {
        "id": "cheetor_sp3_power_burn",
        "t": "power_gain",
        "tm": "",
        "tr": ["onHit"],
        "uit": ["onHit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "level=Special3",
        "trr": "repeat",
        "c": 1.0,
        "m": -9.0,
        "d": 0.5,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "power_burn_debuff",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_cheetor_sp3_power_burn"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_sp3_burn)
    validate_appear(appr_sp3_burn)
    mods["cheetor_sp3_power_burn"] = mod_sp3_burn
    appears["appr_cheetor_sp3_power_burn"] = appr_sp3_burn

    return mods, appears, buffs
