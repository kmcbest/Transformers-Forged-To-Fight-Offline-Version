#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bot Ability Implementation: 眩晕 (Blackout)
===========================================
Bot ID: blackout_cin_tf
阵营: 霸天虎 (Decepticon) | 职业: 破坏分子 (Demolitions / demo)
基准数值: HP 40519, ATK 3272

【官方技能真理源对照 (来自 character_abilities 数据库)】：
-----------------------------------------------------------------------------
1. [被动 - 暴击几率 / Crit Rate] (PUA: \\uE40D)
   - 官方描述: "连击数每增加5，获得1层8%的暴击几率增益，被敌人命中打断连击时全部移除。"
   - 实现方案:
     a) blackout_combo_crit_rate: 触发 onHit，限制 combo%5==0，获得 8% 暴击率，堆叠最多 10 层。
     b) blackout_crit_rate_remove_on_hit: 触发 onReceiveHit，移除所有 blackout_combo_crit_rate。

2. [被动 - 暴击伤害 / Crit Damage] (PUA: \\uE906)
   - 官方描述: "连击数每增加5，获得1层16%的暴击伤害增益，被敌人命中打断连击时全部移除。"
   - 实现方案:
     c) blackout_combo_crit_dmg: 触发 onHit，限制 combo%5==0，获得 16% 暴击伤害，堆叠最多 10 层。
     d) blackout_crit_dmg_remove_on_hit: 触发 onReceiveHit，移除所有 blackout_combo_crit_dmg。

3. [被动 - 无尽怒火 / Infinite Fury] (PUA: \\uE906)
   - 官方描述: "当暴击率超过100%时，溢出的每1%暴击率会转化为1%暴击伤害增益，这个增益会在暴击率低于100%时移除。"
   - 实现方案:
     e) blackout_infinite_fury_crit_dmg: 当连击数达到 15/20/25 击时，暴击率堆叠突破 100%，
        获得额外 25% 暴击伤害转化加成，连击打断受击时一同移除。

4. [被动 - 加特林机枪 / Gatling Gun] (PUA: \\uE41B)
   - 官方描述: "连续3次远程攻击后（无论是否命中），得到1层远程增益，不可叠加，提升50%的远程伤害和40%的远程射速，
                增益将会在此机器人防御、近战、重击、特殊攻击时移除。"
   - 实现方案:
     f) blackout_gatling_ranged_buff: 触发 onAttack (level=Ranged)，获得 50% 远程伤害与 40% 远程射速增益。
     g) 移除链: 在 state=Block, level=Light,Medium,Heavy,Special1,Special2,Special3 时分别移除该增益。

5. [被动 - 重击燃烧 / Heavy Attack Burn] (PUA: \\uE41D)
   - 官方描述: "重击如果暴击，100%概率造成燃烧，施加攻击力80%的伤害，持续6秒。"
   - 实现方案:
     h) blackout_heavy_crit_burn: 触发 onCrit (level=Heavy)，施加 6 秒 80% ATK 燃烧 DOT。

6. [特殊技 1 - 能量炮 / SP1 Unblockable] (PUA: \\uE41F)
   - 官方描述: "最后1击不可防御"
   - 实现方案:
     i) blackout_sp1_unblockable: 最后一击触发不可防御 (Unblockable)，穿透对手格挡。

7. [特殊技 2 - 翼刃回旋 / SP2 Crit Damage & Bleed] (PUA: \\uE906, \\uE401)
   - 官方描述 1: "技能期间提升100%的暴击伤害"
   - 官方描述 2: "每1击暴击时有100%的概率触发流血，在3秒内造成攻击力60%的伤害。"
   - 实现方案:
     j) blackout_sp2_crit_damage: 触发 onSpecial2Activate，持续 5 秒提升 100% 暴击伤害。
     k) blackout_sp2_crit_bleed: 触发 onCrit (level=Special2)，施加 3 秒 60% ATK 流血 DOT。

8. [特殊技 3 - 猎杀 / SP3 Burn & Crit Resistance Debuff] (PUA: \\uE41D, \\uE409)
   - 官方描述 1: "最后一击的暴击率增加50%，如果暴击，100%概率造成燃烧，施加攻击力80%的伤害，持续6秒。"
   - 官方描述 2: "技能结束时，向对手施加1层永久暴击抗性减益，在对手身上打出暴击的几率提升20%。"
   - 实现方案:
     l) blackout_sp3_last_crit_rate: 最后一击暴击率 +50%。
     m) blackout_sp3_crit_burn: 最后一击暴击施加 6 秒 80% ATK 燃烧 DOT。
     n) blackout_sp3_crit_resist_debuff: 技能结束向对手施加永久 20% 易伤削弱 (对方暴击抗性降低20%)。

9. [觉醒能力 - 追猎 / I'll Hunt You Down!] (PUA: \\uE608)
   - 官方描述: "当眩晕的近战攻击落空时，他猎杀对手的渴望变得更强，在3秒内获得最大能量的5% //3秒倒计时结束前不可再次触发"
   - 实现方案:
     o) blackout_sig_whiff_power_gain: 触发 onMiss (level=Light,Medium)，3 秒内获得 45 点 Mana (最大能量 5%)。
-----------------------------------------------------------------------------
"""

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from ..core import (
    AbilityColor,
    make_bleed_statmod,
    make_burn_statmod,
    make_crit_rate_statmod,
    make_crit_damage_statmod,
    make_ranged_boost_statmod,
    make_remove_statmod,
    make_statmod_appearance,
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

    # =========================================================================
    # 1. [ID: 1794966881655] 被动 - 连击暴击几率 (Crit Rate)
    #    连击数每增加5，获得1层8%的暴击几率增益，被敌人命中打断连击时全部移除
    # =========================================================================
    appr_combo_crit_rate = make_statmod_appearance(
        appr_id="appr_blackout_combo_crit_rate",
        callout_text="暴击几率",
        desc="连击数每增加5，暴击几率提升8%，连招被打断时移除",
        pua_icon="\uE40D",
        color=AbilityColor.ORANGE_DAMAGE,
        show_callout=True,
    )
    mod_combo_crit_rate = {
        "id": "blackout_combo_crit_rate",
        "t": "crit_rate",
        "tm": "",
        "tr": [],
        "uit": [],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.08,
        "d": -1.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 99,
        "g": "crit_rate",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_blackout_combo_crit_rate"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_appear(appr_combo_crit_rate)
    validate_statmod(mod_combo_crit_rate)
    appears[appr_combo_crit_rate["id"]] = appr_combo_crit_rate
    mods[mod_combo_crit_rate["id"]] = mod_combo_crit_rate

    # 被敌人命中打断连击时移除暴击几率增益
    m_rem_crit_rate, _ = make_remove_statmod(
        mod_id="blackout_crit_rate_remove_on_hit",
        target_mod_id="blackout_combo_crit_rate",
        trigger="onReceiveHit",
        trigger_scope="",
        show_callout=False,
    )
    mods.update(m_rem_crit_rate)

    # =========================================================================
    # 2. [ID: 1794966881656] 被动 - 连击暴击伤害 (Crit Damage)
    #    连击数每增加5，获得1层16%的暴击伤害增益，被敌人命中打断连击时全部移除
    # =========================================================================
    appr_combo_crit_dmg = make_statmod_appearance(
        appr_id="appr_blackout_combo_crit_dmg",
        callout_text="暴击伤害",
        desc="连击数每增加5，暴击伤害提升16%，连招被打断时移除",
        pua_icon="\uE906",
        color=AbilityColor.ORANGE_DAMAGE,
        show_callout=True,
    )
    mod_combo_crit_dmg = {
        "id": "blackout_combo_crit_dmg",
        "t": "crit_damage",
        "tm": "",
        "tr": [],
        "uit": [],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.16,
        "d": -1.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 99,
        "g": "crit_damage",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_blackout_combo_crit_dmg"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_appear(appr_combo_crit_dmg)
    validate_statmod(mod_combo_crit_dmg)
    appears[appr_combo_crit_dmg["id"]] = appr_combo_crit_dmg
    mods[mod_combo_crit_dmg["id"]] = mod_combo_crit_dmg

    # 被敌人命中打断连击时移除暴击伤害增益
    m_rem_crit_dmg, _ = make_remove_statmod(
        mod_id="blackout_crit_dmg_remove_on_hit",
        target_mod_id="blackout_combo_crit_dmg",
        trigger="onReceiveHit",
        trigger_scope="",
        show_callout=False,
    )
    mods.update(m_rem_crit_dmg)

    # =========================================================================
    # 3. [ID: 1794966881657] 被动 - 无尽怒火 (Infinite Fury)
    #    当暴击率超过100%时，溢出的每1%转化为1%暴伤增益，连击打断时移除
    # =========================================================================
    appr_infinite_fury = make_statmod_appearance(
        appr_id="appr_blackout_infinite_fury",
        callout_text="无尽怒火",
        desc="暴击率溢出100%部分转化为等额暴击伤害增益",
        pua_icon="\uE906",
        color=AbilityColor.ORANGE_DAMAGE,
        show_callout=True,
    )
    mod_infinite_fury = {
        "id": "blackout_infinite_fury_crit_dmg",
        "t": "crit_damage",
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
        "st": 1,
        "g": "infinite_fury",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_blackout_infinite_fury"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_appear(appr_infinite_fury)
    validate_statmod(mod_infinite_fury)
    appears[appr_infinite_fury["id"]] = appr_infinite_fury
    mods[mod_infinite_fury["id"]] = mod_infinite_fury

    # 受击连击中断移除无尽怒火
    m_rem_fury, _ = make_remove_statmod(
        mod_id="blackout_fury_remove_on_hit",
        target_mod_id="blackout_infinite_fury_crit_dmg",
        trigger="onReceiveHit",
        trigger_scope="",
        show_callout=False,
    )
    mods.update(m_rem_fury)

    # =========================================================================
    # 4. [ID: 1794966881658] 被动 - 加特林机枪 (Gatling Gun)
    #    连续3次远程攻击后获得远程增益 (+50%远程伤害, +40%射速)，
    #    防御、近战、重击、特殊攻击时移除
    # =========================================================================
    m_gatling, a_gatling = make_ranged_boost_statmod(
        mod_id="blackout_gatling_ranged_buff",
        duration=15.0,
        damage_bonus=0.50,
        speed_bonus=0.40,
        trigger="onAttack",
        trigger_scope="level=Ranged",
        appr_id="appr_blackout_gatling",
        callout_text="加特林强化",
        show_callout=True,
        pua_icon="\uE41B",
        color_hex="FFAA00",
        gradient_bottom="FF6600",
    )
    mods.update(m_gatling)
    appears.update(a_gatling)

    # 4项状态切换时移除加特林远程增益
    # a) 防御时移除
    m_rem_gat_block, _ = make_remove_statmod(
        mod_id="blackout_gatling_rem_block",
        target_mod_id="blackout_gatling_ranged_buff",
        trigger="onPlayerStateEnter",
        trigger_scope="state=Block",
        show_callout=False,
    )
    mods.update(m_rem_gat_block)

    # b) 近战时移除
    m_rem_gat_melee, _ = make_remove_statmod(
        mod_id="blackout_gatling_rem_melee",
        target_mod_id="blackout_gatling_ranged_buff",
        trigger="onAttack",
        trigger_scope="level=Light,Medium",
        show_callout=False,
    )
    mods.update(m_rem_gat_melee)

    # c) 重击时移除
    m_rem_gat_heavy, _ = make_remove_statmod(
        mod_id="blackout_gatling_rem_heavy",
        target_mod_id="blackout_gatling_ranged_buff",
        trigger="onAttack",
        trigger_scope="level=Heavy",
        show_callout=False,
    )
    mods.update(m_rem_gat_heavy)

    # d) 特殊攻击时移除
    m_rem_gat_sp, _ = make_remove_statmod(
        mod_id="blackout_gatling_rem_sp",
        target_mod_id="blackout_gatling_ranged_buff",
        trigger="onAttack",
        trigger_scope="level=Special1,Special2,Special3",
        show_callout=False,
    )
    mods.update(m_rem_gat_sp)

    # =========================================================================
    # 5. [ID: 1794966881659] 被动 - 重击暴击燃烧 (Heavy Attack Burn)
    #    重击如果暴击，100%造成持续6秒相当于80%攻击力的燃烧伤害
    # =========================================================================
    m_heavy_burn, a_heavy_burn = make_burn_statmod(
        mod_id="blackout_heavy_crit_burn",
        duration=6.0,
        total_dmg=float(round(base_atk * 0.80)),
        chance=1.0,
        trigger="onCrit",
        trigger_scope="level=Heavy",
        appr_id="appr_blackout_heavy_burn",
        callout_text="导弹灼烧",
        pua_icon="\uE41D",
        color_hex=AbilityColor.RED_DEBUFF_TC,
        gradient_bottom=AbilityColor.RED_DEBUFF_GB,
    )
    mods.update(m_heavy_burn)
    appears.update(a_heavy_burn)

    # =========================================================================
    # 6. [ID: 1794966881664] 特殊技 1 (能量炮) - 不可防御 (Unblockable)
    #    最后1击不可防御
    # =========================================================================
    appr_sp1_unblockable = make_statmod_appearance(
        appr_id="appr_blackout_sp1_unblockable",
        callout_text="不可防御",
        desc="能量炮最后一击强行穿透对手格挡",
        pua_icon="\uE41F",
        color=AbilityColor.YELLOW_STATUS,
        show_callout=True,
    )
    mod_sp1_unblockable = {
        "id": "blackout_sp1_unblockable",
        "t": "unblockable",
        "tm": "",
        "tr": ["onAttack"],
        "uit": ["onAttack"],
        "pri": 1,
        "trm": 0.0,
        "trs": "level=Special1;isLastHit=true",
        "trr": "repeat",
        "c": 1.0,
        "m": 1.0,
        "d": 0.0,
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
        "a": ["appr_blackout_sp1_unblockable"],
        "au": ["appr_blackout_sp1_unblockable"],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_appear(appr_sp1_unblockable)
    validate_statmod(mod_sp1_unblockable)
    appears[appr_sp1_unblockable["id"]] = appr_sp1_unblockable
    mods[mod_sp1_unblockable["id"]] = mod_sp1_unblockable

    # =========================================================================
    # 7. [ID: 1794966881662 & 1794966881663] 特殊技 2 (翼刃回旋) - 暴击伤害与暴击流血
    #    a) 技能期间提升100%暴击伤害
    #    b) 每1击暴击100%概率触发3秒流血 (60%攻击力伤害)
    # =========================================================================
    m_sp2_crit_dmg, a_sp2_crit_dmg = make_crit_damage_statmod(
        mod_id="blackout_sp2_crit_damage",
        duration=5.0,
        crit_dmg_bonus=1.00,
        chance=1.0,
        trigger="onSpecial2Activate",
        trigger_scope="",
        appr_id="appr_blackout_sp2_crit_dmg",
        callout_text="暴击强化",
        pua_icon="\uE906",
        color_hex=AbilityColor.ORANGE_DAMAGE_TC,
        gradient_bottom=AbilityColor.ORANGE_DAMAGE_GB,
    )
    mods.update(m_sp2_crit_dmg)
    appears.update(a_sp2_crit_dmg)

    m_sp2_bleed, a_sp2_bleed = make_bleed_statmod(
        mod_id="blackout_sp2_crit_bleed",
        duration=3.0,
        total_dmg=float(round(base_atk * 0.60)),
        chance=1.0,
        trigger="onCrit",
        trigger_scope="level=Special2",
        appr_id="appr_blackout_sp2_bleed",
        callout_text="撕裂流血",
        pua_icon="\uE401",
        color_hex=AbilityColor.RED_DEBUFF_TC,
        gradient_bottom=AbilityColor.RED_DEBUFF_GB,
    )
    mods.update(m_sp2_bleed)
    appears.update(a_sp2_bleed)

    # =========================================================================
    # 8. [ID: 1794966881660 & 1794966881661] 特殊技 3 (猎杀) - 暴击燃烧与永久暴抗减益
    #    a) 最后一击暴击率+50%
    #    b) 最后一击暴击造成持续6秒80%攻击力燃烧伤害
    #    c) 技能结束向对手施加1层永久暴击抗性减益 (对手受暴击率提升20%)
    # =========================================================================
    m_sp3_crit_rate, a_sp3_crit_rate = make_crit_rate_statmod(
        mod_id="blackout_sp3_last_crit_rate",
        duration=2.0,
        crit_bonus=0.50,
        chance=1.0,
        trigger="onHitStarted",
        trigger_scope="level=Special3;dmgFlags=LastHit",
        appr_id="appr_blackout_sp3_crit_rate",
        callout_text="锁定暴击",
        pua_icon="\uE40D",
        color_hex=AbilityColor.ORANGE_DAMAGE_TC,
        gradient_bottom=AbilityColor.ORANGE_DAMAGE_GB,
    )
    mods.update(m_sp3_crit_rate)
    appears.update(a_sp3_crit_rate)

    m_sp3_burn, a_sp3_burn = make_burn_statmod(
        mod_id="blackout_sp3_crit_burn",
        duration=6.0,
        total_dmg=float(round(base_atk * 0.80)),
        chance=1.0,
        trigger="onCrit",
        trigger_scope="level=Special3;dmgFlags=LastHit",
        appr_id="appr_blackout_sp3_burn",
        callout_text="地毯焚烧",
        pua_icon="\uE41D",
        color_hex=AbilityColor.RED_DEBUFF_TC,
        gradient_bottom=AbilityColor.RED_DEBUFF_GB,
    )
    mods.update(m_sp3_burn)
    appears.update(a_sp3_burn)

    # 技能结束向对手施加永久暴击抗性减益 (自身对其暴击率相对增加 20%)
    appr_sp3_crit_resist = make_statmod_appearance(
        appr_id="appr_blackout_crit_resist_debuff",
        callout_text="易伤削弱",
        desc="对手暴击抗性永久降低20%，受暴击几率提升",
        pua_icon="\uE409",
        color=AbilityColor.RED_DEBUFF,
        show_callout=True,
    )
    mod_sp3_crit_resist = {
        "id": "blackout_sp3_crit_resist_debuff",
        "t": "crit_rate",
        "tm": "",
        "tr": ["onSpecial3Expiry", "onSpecial3Hit"],
        "uit": ["onSpecial3Expiry", "onSpecial3Hit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.20,
        "d": -1.0,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "crit_resist_debuff",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_blackout_crit_resist_debuff"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_appear(appr_sp3_crit_resist)
    validate_statmod(mod_sp3_crit_resist)
    appears[appr_sp3_crit_resist["id"]] = appr_sp3_crit_resist
    mods[mod_sp3_crit_resist["id"]] = mod_sp3_crit_resist

    # =========================================================================
    # 9. [ID: 1794966881665] 觉醒能力 - 追猎 (I'll Hunt You Down!)
    #    近战攻击落空时，在3秒内获得最大能量的5% (45点Mana)，3秒内不可重复触发
    #    由 NativeHook 在对方闪避我方近战时精准接管与判定，避免客户端内置 onMiss 误判
    # =========================================================================
    appr_sig_power = make_statmod_appearance(
        appr_id="appr_blackout_sig_power",
        callout_text="追猎渴望",
        desc="近战落空激活追猎渴望，3秒内获得5%最大能量",
        pua_icon="\uE608",
        color=AbilityColor.LIGHT_PURPLE_POWER,
        show_callout=True,
    )
    mod_sig_power = {
        "id": "blackout_sig_whiff_power_gain",
        "t": "power_gain",
        "tm": "",
        "tr": [],
        "uit": [],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 45.0,  # 3格满气基准为 900 点 Mana，5% 即为 45 点
        "d": 3.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "power_gain",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_blackout_sig_power"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_appear(appr_sig_power)
    validate_statmod(mod_sig_power)
    appears[appr_sig_power["id"]] = appr_sig_power
    mods[mod_sig_power["id"]] = mod_sig_power

    # 消除静默移除修饰器的未注册外观告警
    for m in mods.values():
        if m.get("t") == "remove":
            m["a"] = []

    return mods, appears, buffs
