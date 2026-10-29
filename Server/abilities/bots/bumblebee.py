#!/usr/bin/env python3
"""
Bot Ability Implementation: 小黄蜂 (Bumblebee)
==============================================
Bot ID: bumblebee_gs_kabam
阵营: 汽车人 (Autobot) | 职业: 侦察兵 (Scout)

【官方技能真理源对照 (来自 character_abilities / priority_abilities 清单)】：
-----------------------------------------------------------------------------
1. [被动 - 近战规避 / Melee Evade] (ID: 2439, pua_icon: 0xe509, category: passive)
   - 官方描述: "后闪会获得一个32%概率的近战规避，无倒计时，触发规避后消耗。"
   - 实现方案:
     bumblebee_dodge_evade_melee: 触发 onPlayerStateEnter, state=Dodge, 32% 概率获得近战规避 buff (duration=0.0),
     规避成功触发后消耗移除。

2. [被动 - 暴击几率增益 / Sidestep Crit Rate] (ID: 2441, pua_icon: 0xe40d, category: passive)
   - 官方描述: "侧闪时获得一个28%的暴击几率增益，最多累积3个。每次小黄蜂命中对手时（无论是否出暴击），消耗一个增益。//被防不消耗增益"
   - 实现方案:
     bumblebee_sidestep_crit_rate: 侧闪获得 28% 暴击率，上限 3 层。
     bumblebee_crit_consume: 命中非格挡攻击消耗 1 层。

3. [觉醒技 - 蜂之勇气 / Bee Brave] (ID: 2445, pua_icon: 0xe608, category: signature)
   - 官方描述: "与敌人处于近战距离时得到能量涌动，每秒自动产生最大能量的1.2%，同时得到10%的近战增益。离开近战距离立即消失。"
   - 实现方案:
     bumblebee_close_power & bumblebee_close_melee: 处于近身状态时每秒自动充能 3.6 点 Mana (1.2%) 并获得 10% 近战加成。

4. [特殊技 1 - 暴击伤害 / SP1 Crit Damage] (ID: 2450, pua_icon: 0xe906, category: sp1)
   - 官方描述: "技能发动过程中暴击伤害提升60%"
   - 实现方案:
     bumblebee_sp1_crit_damage: SP1 激活期间暴击伤害 +60%。

5. [特殊技 2 - 能量锁定 / SP2 Power Lock] (ID: 2451, pua_icon: 0xe523, category: sp2)
   - 官方描述: "第一击命中时100%概率触发能量锁定，阻止对方获得能量，持续10秒"
   - 实现方案:
     bumblebee_sp2_power_lock: SP2 首段命中施加 10 秒能量锁定。

6. [特殊技 3 - 暴击几率增益 / SP3 Crit Rate Stacks] (ID: 2452, pua_icon: 0xe40d, category: sp3)
   - 官方描述: "技能完成后获得20个暴击几率增益，提升28%的暴击几率，每次小黄蜂命中对手时（无论是否出暴击），消耗一个增益。//被防不消耗增益"
   - 实现方案:
     bumblebee_sp3_crit_rate: SP3 最后一击完成获得 20 层暴击增益。
-----------------------------------------------------------------------------
"""

from ..core import (
    make_evade_grant_statmod,
    make_evade_consume_statmod,
    make_crit_rate_statmod,
    make_crit_damage_statmod,
    make_power_lock_statmod,
    make_attack_boost_statmod,
    validate_statmod,
    validate_appear,
    validate_color_code,
)
from ..registry import register_bot

BOT_ID = "bumblebee_gs_kabam"


@register_bot(BOT_ID, name_zh="小黄蜂", desc="侦察兵，后闪近战规避、侧闪与SP3暴击堆叠、近距蜂之勇气能量涌动、SP1暴伤增强、SP2能量锁定")
def build_bumblebee_abilities(base_hp: float = 30000.0, base_atk: float = 3000.0):
    """
    根据基准属性生成小黄蜂专属全套能力修饰器。
    基准 5星50级 HP = 30000.0, ATK = 3000.0
    """
    mods = {}
    appears = {}
    buffs = {}

    # -------------------------------------------------------------------------
    # 1. 获得规避能力 (ID: 2439)
    # -------------------------------------------------------------------------
    m_grant, a_grant = make_evade_grant_statmod(
        mod_id="bumblebee_dodge_evade_melee",
        evade_type="melee",
        grant_chance=1.0,               # 获得概率 100%
        evade_chance=0.32,              # 触发规避几率 32%
        duration=0.0,                   # 无倒计时
        trigger="onPlayerStateEnter",
        trigger_scope="state=Dodge",    # 后闪触发
        appr_id="appr_bumblebee_dodge_evade_melee",
        callout_text="近战规避",
        pua_icon="\uE509",              # 近战规避矢量图标
        color_hex="10B981",             # 绿色
        gradient_bottom="059669",
        show_callout=False,
    )
    mods.update(m_grant)
    appears.update(a_grant)

    # 规避成功触发后的消耗与呼出大字
    m_consume, a_consume = make_evade_consume_statmod(
        mod_id="bumblebee_evade_consume",
        target_mod_id="bumblebee_dodge_evade_melee",
        evade_type="melee",
        callout_text="规避",
        appr_id="appr_bumblebee_evade_consume",
        pua_icon="\uE509",
        color_hex="10B981",
        gradient_bottom="059669",
        show_callout=True,
    )
    mods.update(m_consume)
    appears.update(a_consume)

    # -------------------------------------------------------------------------
    # 2. 侧闪暴击几率增益 (ID: 2441)
    # 侧闪时获得 28% 暴击几率增益，最多 3 层。命中消耗 1 层。
    # -------------------------------------------------------------------------
    m_crit_side, a_crit_side = make_crit_rate_statmod(
        mod_id="bumblebee_sidestep_crit_rate",
        duration=0.0,
        crit_bonus=0.28,
        chance=1.0,
        trigger="onPlayerStateEnter",
        trigger_scope="state=Sidestep",
        appr_id="appr_bumblebee_sidestep_crit_rate",
        callout_text="暴击几率",
        pua_icon="\uE40D",
        color_hex="FF8800",
        gradient_bottom="D97706",
    )
    m_crit_side["bumblebee_sidestep_crit_rate"]["st"] = 3
    mods.update(m_crit_side)
    appears.update(a_crit_side)

    # 命中消耗暴击增益 (非被防)
    mod_consume_crit = {
        "id": "bumblebee_crit_consume",
        "t": "remove",
        "tm": "bumblebee_sidestep_crit_rate",
        "tr": ["onHit"],
        "uit": ["onHit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "is_blocked=False",
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
        "g": "",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": [],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_consume_crit)
    mods["bumblebee_crit_consume"] = mod_consume_crit

    # -------------------------------------------------------------------------
    # 3. 觉醒技 - 蜂之勇气 (ID: 2445)
    # 靠近敌人时能量涌动每秒 1.2% (3.6 Mana)，近战攻击力 +10%
    # -------------------------------------------------------------------------
    validate_color_code("FFE000", "bee_brave_tc")
    validate_color_code("D97706", "bee_brave_gb")
    appr_brave = {
        "id": "appr_bumblebee_bee_brave",
        "a": "蜂之勇气",
        "s": "蜂之勇气",
        "l": "近战距离时激活能量涌动，每秒获得1.2%最大能量",
        "ss": "蜂之勇气",
        "t": "\uE608",
        "f": "",
        "st": "蜂之勇气",
        "ps": "蜂之勇气",
        "pl": "蜂之勇气生效中",
        "tc": "FFE000",
        "gt": "FFE000",
        "gb": "D97706",
    }
    validate_appear(appr_brave)
    appears["appr_bumblebee_bee_brave"] = appr_brave

    mod_brave_power = {
        "id": "bumblebee_close_power",
        "t": "power_gain",
        "tm": "",
        "tr": ["onPlayerStateEnter"],
        "uit": ["onPlayerStateEnter"],
        "pri": 0,
        "trm": 0.0,
        "trs": "distance=Close",
        "trr": "repeat",
        "c": 1.0,
        "m": 3.6,
        "d": 0.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "bee_brave_power",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_bumblebee_bee_brave"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_brave_power)
    mods["bumblebee_close_power"] = mod_brave_power

    m_brave_melee, a_brave_melee = make_attack_boost_statmod(
        mod_id="bumblebee_close_melee",
        duration=0.0,
        attack_bonus=0.10,
        chance=1.0,
        trigger="onPlayerStateEnter",
        trigger_scope="distance=Close",
        appr_id="appr_bumblebee_close_melee",
        callout_text="近战增益",
        pua_icon="\uE406",
        color_hex="FF8800",
        gradient_bottom="D97706",
    )
    mods.update(m_brave_melee)
    appears.update(a_brave_melee)

    # -------------------------------------------------------------------------
    # 4. 特殊技 1 - 暴击伤害提升 60% (ID: 2450)
    # -------------------------------------------------------------------------
    m_sp1_crit, a_sp1_crit = make_crit_damage_statmod(
        mod_id="bumblebee_sp1_crit_damage",
        duration=0.0,
        crit_dmg_bonus=0.60,
        chance=1.0,
        trigger="onSpecial1Activate",
        trigger_scope="level=Special1",
        appr_id="appr_bumblebee_sp1_crit_damage",
        callout_text="暴击伤害",
        pua_icon="\uE906",
        color_hex="FF8800",
        gradient_bottom="D97706",
    )
    mods.update(m_sp1_crit)
    appears.update(a_sp1_crit)

    # -------------------------------------------------------------------------
    # 5. 特殊技 2 - 能量锁定 10.0s (ID: 2451)
    # -------------------------------------------------------------------------
    m_sp2_lock, a_sp2_lock = make_power_lock_statmod(
        mod_id="bumblebee_sp2_power_lock",
        duration=10.0,
        chance=1.0,
        trigger="onSpecial2Hit",
        trigger_scope="hitIndex=0",
        appr_id="appr_bumblebee_sp2_power_lock",
        callout_text="能量锁定",
        pua_icon="\uE523",
        color_hex="EF4444",
        gradient_bottom="B91C1C",
    )
    mods.update(m_sp2_lock)
    appears.update(a_sp2_lock)

    # -------------------------------------------------------------------------
    # 6. 特殊技 3 - 20个暴击几率增益 (ID: 2452)
    # -------------------------------------------------------------------------
    m_sp3_crit, a_sp3_crit = make_crit_rate_statmod(
        mod_id="bumblebee_sp3_crit_rate",
        duration=0.0,
        crit_bonus=0.28,
        chance=1.0,
        trigger="onSpecial3Activate",
        trigger_scope="dmgFlags=LastHit",
        appr_id="appr_bumblebee_sp3_crit_rate",
        callout_text="暴击几率",
        pua_icon="\uE40D",
        color_hex="FF8800",
        gradient_bottom="D97706",
    )
    m_sp3_crit["bumblebee_sp3_crit_rate"]["st"] = 20
    mods.update(m_sp3_crit)
    appears.update(a_sp3_crit)

    return mods, appears, buffs
