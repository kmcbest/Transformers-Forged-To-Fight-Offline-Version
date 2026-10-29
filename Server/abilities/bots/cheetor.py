#!/usr/bin/env python3
"""
Bot Ability Implementation: 黄豹 (Cheetor)
===========================================
Bot ID: cheetor_bw_transmetal
阵营: 巨无霸 (Maximal) | 职业: 侦察兵 (Scout)

【官方技能真理源对照 (来自 character_abilities 数据库与优先实现清单)】：
-----------------------------------------------------------------------------
1. [被动 - 能量守护 / Power Guard] (ID: 2472, pua_icon: 0xe608)
   - 官方描述: "黄豹对吸取能量的技能（能量流失、能量燃烧）免疫，此类技能无法扣减黄豹的能量"
   - 实现方案: cheetor_power_guard: 能量守护被动，免疫能量流失与能量燃烧扣减。

2. [被动 - 暴击流血 / Critical Bleed] (ID: 2473, pua_icon: 0xe401)
   - 官方描述: "近战攻击出暴击时，有45%的概率触发流血，造成攻击力65%的伤害，持续4秒。"
   - 实现方案: cheetor_crit_bleed: 触发 onCrit，限制近战，造成 65% ATK 4.0 秒流血。

3. [被动 - 能量获取 / Power Gain] (ID: 2474, pua_icon: 0xe608)
   - 官方描述: "L4或者M2命中对手的时候，在1秒内获得最大能量槽的2.5%"
   - 实现方案: cheetor_combo_power_gain: 触发 onHit，限制 level=Light4,Medium2，1秒内获得 2.5% 最大能量。

4. [被动 - 重击规避远程 / Heavy Evade Range] (ID: 2475, pua_icon: 0xe518)
   - 官方描述: "黄豹重击过程中有35%的概率穿透对方的基础远程和远程重击，如果没有触发穿透，则100%的概率触发规避"
   - 实现方案: cheetor_heavy_evade_ranged: 触发 onHit / onStateEnter 重击期间获得远程穿透与规避。

5. [特殊技1 - 阻止修复 / SP1 Heal Block] (ID: 2462, pua_icon: 0xe90c)
   - 官方描述: "施加阻止修复，禁用对方所有回血能力，直到对方流血状态解除。"
   - 实现方案: cheetor_sp1_heal_block: 限制 level=Special1，对目标施加禁疗。

6. [特殊技1 - 流血 / SP1 Bleed] (ID: 2476, pua_icon: 0xe401)
   - 官方描述: "最后一击命中时100%概率触发流血，施加攻击力100%的伤害，持续8秒"
   - 实现方案: cheetor_sp1_bleed: 触发 onHit，限制 level=Special1，100% 概率施加 100% ATK 8.0 秒流血。

7. [特殊技2 - 伤害放大 / SP2 Damage Increase] (ID: 2463, pua_icon: 0xe406)
   - 官方描述: "对手能量越少，该攻击伤害越大，最大造成50%的额外伤害。"
   - 实现方案: cheetor_sp2_dmg_amp: SP2 激活期间伤害提升最高 50%。

8. [特殊技2 - 能量功率 / SP2 Power Rate] (ID: 2477, pua_icon: 0xe608)
   - 官方描述: "获得能量功率增益，能量获取量增加50%，持续12秒"
   - 实现方案: cheetor_sp2_power_buff: 触发 onHit，限制 level=Special2，能量获取量增加 50%，持续 12 秒。

9. [特殊技3 - 伤害放大 / SP3 Damage Increase] (ID: 2478, pua_icon: 0xe406)
   - 官方描述: "对手能量越少，该攻击伤害越大，最大造成100%的额外伤害。"
   - 实现方案: cheetor_sp3_dmg_amp: SP3 释放时根据残气增幅，最大 +100% 伤害。

10. [特殊技3 - 能量锁定 / SP3 Power Lock] (ID: 2479, pua_icon: 0xe523)
    - 官方描述: "技能完成时100%概率触发能量锁定，阻止对方获得能量，持续10秒"
    - 实现方案: cheetor_sp3_power_lock: 限制 level=Special3，施加 10.0 秒能量锁定。

11. [特殊技3 - 能量燃烧 / SP3 Power Burn] (ID: 2480, pua_icon: 0xe607)
    - 官方描述: "0.5秒内扣减对方最大能量的3%"
    - 实现方案: cheetor_sp3_power_burn: 限制 level=Special3，0.5 秒内扣除 3% 最大能量。

12. [觉醒技 - 野生突击 / Feral Strike] (ID: 2461, pua_icon: 0xe160)
    - 官方描述: "每充满一格能量，黄豹得到4秒的野生突击状态（黄色图标），暴击率+40%，破甲，对手禁闪避与技能，自身25%规避近战"
-----------------------------------------------------------------------------
"""

from ..core import (
    AbilityColor,
    make_bleed_statmod,
    make_statmod_appearance,
    validate_statmod,
    validate_appear,
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
    # 1. 能量守护 (ID: 2472): 免疫能量流失与能量燃烧扣减
    # -------------------------------------------------------------------------
    appr_pwr_guard = make_statmod_appearance(
        appr_id="appr_cheetor_power_guard",
        callout_text="能量守护",
        desc="免疫能量流失与能量燃烧技能，无法被对手扣减能量",
        pua_icon="\uE608",
        color=AbilityColor.LIGHT_PURPLE_POWER,
        show_callout=True,
    )
    mod_pwr_guard = {
        "id": "cheetor_power_guard",
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
        "d": 0.0,
        "s": "none",
        "ta": "self",
        "mt": "passive",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "power_guard",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_cheetor_power_guard"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_pwr_guard)
    validate_appear(appr_pwr_guard)
    mods["cheetor_power_guard"] = mod_pwr_guard
    appears["appr_cheetor_power_guard"] = appr_pwr_guard

    # -------------------------------------------------------------------------
    # 2. 暴击流血 4.0s (65% ATK, 45% 概率) (ID: 2473)
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
    # 3. L4 与 M2 命中连击能量获取 2.5% (7.5 点 Mana) (ID: 2474)
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
    # 4. 重击规避远程 (ID: 2475): 重击期间 35% 穿透远程，未穿透 100% 规避
    # -------------------------------------------------------------------------
    appr_heavy_evade = make_statmod_appearance(
        appr_id="appr_cheetor_heavy_evade_ranged",
        callout_text="远程穿透",
        desc="重击过程中35%概率穿透远程攻击，否则100%触发闪避规避",
        pua_icon="\uE518",
        color=AbilityColor.YELLOW_STATUS,
        show_callout=True,
    )
    mod_heavy_evade = {
        "id": "cheetor_heavy_evade_ranged",
        "t": "evade_ranged",
        "tm": "",
        "tr": ["onHit"],
        "uit": ["onHit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "level=Heavy",
        "trr": "repeat",
        "c": 1.0,
        "m": 1.0,
        "d": 1.5,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "penetrate_buff",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_cheetor_heavy_evade_ranged"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_heavy_evade)
    validate_appear(appr_heavy_evade)
    mods["cheetor_heavy_evade_ranged"] = mod_heavy_evade
    appears["appr_cheetor_heavy_evade_ranged"] = appr_heavy_evade

    # -------------------------------------------------------------------------
    # 5. SP1：阻止修复 (Heal Block) (ID: 2462)
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
    # 6. SP1：收招流血 8.0s (100% ATK) (ID: 2476)
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
    # 7. SP2：能量功率增益 +50% 持续 12 秒 (ID: 2477)
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
    # 8. SP3：伤害放大 (ID: 2478) - 对手能量越少伤害越大，最大 +100%
    # -------------------------------------------------------------------------
    appr_sp3_amp = make_statmod_appearance(
        appr_id="appr_cheetor_sp3_dmg_amp",
        callout_text="伤害放大",
        desc="对手能量越少造成额外伤害越高，最大造成100%额外伤害",
        pua_icon="\uE406",
        color=AbilityColor.ORANGE_DAMAGE,
        show_callout=True,
    )
    mod_sp3_amp = {
        "id": "cheetor_sp3_dmg_amp",
        "t": "attack_buff",
        "tm": "",
        "tr": ["onSpecial3Activate"],
        "uit": ["onSpecial3Activate"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 1.00,
        "d": 4.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "damage_amp",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_cheetor_sp3_dmg_amp"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_sp3_amp)
    validate_appear(appr_sp3_amp)
    mods["cheetor_sp3_dmg_amp"] = mod_sp3_amp
    appears["appr_cheetor_sp3_dmg_amp"] = appr_sp3_amp

    # -------------------------------------------------------------------------
    # 9. SP3：能量锁定 10 秒 (ID: 2479)
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
    # 10. SP3：能量燃烧 3% (9 点 Mana) (ID: 2480)
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

    # -------------------------------------------------------------------------
    # 11. 觉醒技：野生突击 (Feral Strike) 4.0s (ID: 2461)
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

    return mods, appears, buffs
