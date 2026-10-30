#!/usr/bin/env python3
"""
Bot Ability Implementation: 打击 (Breakdown)
===========================================
Bot ID: breakdown_gs
阵营: 霸天虎 (Decepticon) | 职业: 格斗系 / 侦察兵 (Brawler / Scout)

【官方技能真理源对照 (来自 character_abilities 数据库与在线优先实现)】：
-----------------------------------------------------------------------------
1. [被动 - 护盾崩解 / Shield Break] (ID: 3504, pua_icon: E807)
   - 官方描述: "成功闪避对方重击时，获得一个护盾崩解增益，提升50%的近战伤害，在近战命中时消耗此增益，清除对方身上所有的护盾并施加攻击力50%的即时伤害。  //橙色图标，无倒计时"
   - 实现方案:
     a) breakdown_shield_break_buff: 闪避对方重击获得 50% 近战增益 (常驻无倒计时)。
     b) breakdown_shield_break_nullify: 近战命中清除对方身上所有护盾 (nullify)。
     c) breakdown_shield_break_dmg: 近战命中施加攻击力 50% 的即时直接伤害。
     d) breakdown_shield_break_consume: 近战命中消耗护盾崩解增益。

2. [觉醒技 - 晚期神经质 / Terminal Paranoia] (ID: 3505, pua_icon: E509)
   - 官方描述: "敌方血量大于50%时，打击获得一个规避增益，40%的概率规避对方近战攻击，成功规避后增益消失，5秒后重新获得。 //先是绿图标，无倒计时，触发规避后变成5秒倒计时的灰图标，再变回绿图标。如果倒计时过程中对方血量跌至50%以下，倒计时结束不再获得。
     敌方血量小于50%时，打击获得一个暴击率增益，提升40%的暴击几率，触发暴击后消失，5秒后重新获得 //先是黄图标，无倒计时，触发暴击后变成5秒倒计时的灰图标，再变回黄图标。如果倒计时过程中对方血量升至50%以上，倒计时结束不再获得。"
   - 实现方案:
     e) breakdown_paranoia_evade: 敌方生命值高于 50% 时获得 40% 近战规避常驻增益，规避后移除并进入 5 秒冷却。
     f) breakdown_paranoia_evade_consume: 规避触发时消耗规避增益。
     g) breakdown_paranoia_crit: 敌方生命值低于 50% 时获得 40% 暴击率常驻增益，暴击后移除并进入 5 秒冷却。
     h) breakdown_paranoia_crit_consume: 暴击触发时消耗暴击增益。

3. [SP1 - 能量流失 / Power Leak] (ID: 3506, pua_icon: E607)
   - 官方描述: "最后一击命中时，50%概率施加能量流失，在5秒内扣除对方最大能量的12%。"
   - 实现方案:
     i) breakdown_sp1_power_leak: SP1 最后一击 50% 概率施加 5 秒能量流失，扣除 12% 最大能量 (0.36 格)。

4. [SP3 - 远程减益 / Ranged Debuff] (ID: 3508, pua_icon: E519)
   - 官方描述: "施加远程减益，降低对手的远程攻击伤害的100%，持续20秒"
   - 实现方案:
     j) breakdown_sp3_ranged_debuff: SP3 命中施加 20 秒远程伤害 -100% 减益。

5. [SP1 - 暴击几率 / Crit Rate] (ID: 3512, pua_icon: E40D)
   - 官方描述: "最后一击命中时，35%的概率得到30%的暴击几率增益，持续8秒"
   - 实现方案:
     k) breakdown_sp1_crit_rate: SP1 最后一击 35% 几率获得 30% 暴击率，持续 8 秒。

6. [被动 - 近战规避 / Melee Evade] (ID: 3513, pua_icon: 0xe509)
   - 官方描述: "L4或M2被防时，有75%的概率获得4秒的近战规避。"
   - 实现方案:
     l) breakdown_block_evade: L4 或 M2 命中对方格挡时 75% 概率获得 4 秒近战规避。

7. [SP2 - 燃烧 / Burn] (ID: 3514, pua_icon: E41D)
   - 官方描述: "最后一击造成燃烧，施加攻击力120%的伤害，持续4秒。"
   - 实现方案:
     m) breakdown_sp2_burn: SP2 最后一击 100% 施加 4 秒燃烧 DOT，造成 120% ATK 火焰能量伤害。

8. [SP2 - 确定性 / Certainty] (ID: 3515, pua_icon: E909)
   - 官方描述: "施加确定性减益，对方下次充满一格能量后，必然立即释放特殊技1，释放后减益消失。//即便有2或3格气，也强制出SP1"
   - 实现方案:
     n) breakdown_sp2_certainty: SP2 最后一击施加 1 层确定性减益，对手下次满气强制释放 SP1。

9. [SP3 - 确定性 / Certainty] (ID: 3516, pua_icon: E909)
   - 官方描述: "施加2层确定性减益，对方下次充满一格能量后，必然立即释放特殊技1，释放后减益消失。//即便有2或3格气，也强制出SP1"
   - 实现方案:
     o) breakdown_sp3_certainty: SP3 命中施加 2 层确定性减益，对手连续 2 次满气强制释放 SP1。
-----------------------------------------------------------------------------
"""

from typing import Dict, Any, Tuple
from ..core import (
    AbilityColor,
    make_power_leak_statmod,
    make_crit_rate_statmod,
    make_burn_statmod,
    make_evade_grant_statmod,
    make_nullify_statmod,
    make_direct_dmg_statmod,
    make_remove_statmod,
    make_statmod_appearance,
    validate_statmod,
    validate_appear,
)
from ..registry import register_bot

BOT_ID = "breakdown_gs"


@register_bot(
    BOT_ID,
    name_zh="打击",
    desc="霸天虎近战狂暴战士，重击闪避护盾崩解破盾重创，晚期神经质双态规避与狂暴暴击，SP1能量流失与暴击率提升，普攻受阻近战规避，SP2致命燃烧与强制释放SP1确定性压制",
)
def build_breakdown_abilities(
    base_hp: float = 34850.0,
    base_atk: float = 3485.0,
) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """
    根据基准属性生成打击 (Breakdown) 全部专属能力修饰器。
    基准 5星50级 HP = 34850.0, ATK = 3485.0
    """
    mods = {}
    appears = {}
    buffs = {
        # 护盾崩解即时额外伤害
        "dmg_direct": {
            "id": "dmg_direct",
            "iconTexture": "",
            "image": "",
            "images3": False,
            "modeAvail": [],
            "scope": "global",
            "valueType": "absolute",
            "displayValue": float(round(base_atk * 0.50)),
            "c": 1,
            "value": float(round(base_atk * 0.50)),
            "buffType": "damage",
            "group": "dmg_direct",
            "p": {"damage_type": "physical"},
            "hasDuration": True,
            "e": 0,
            "time": {"amount": 0.5},
            "loc_name": "shield_break_dmg",
            "loc_desc": "shield_break_dmg",
        },
        # SP2 燃烧持续伤害 DOT
        "dmg_burn": {
            "id": "dmg_burn",
            "iconTexture": "",
            "image": "",
            "images3": False,
            "modeAvail": [],
            "scope": "global",
            "valueType": "absolute",
            "displayValue": float(round(base_atk * 1.20)),
            "c": 1,
            "value": float(round(base_atk * 1.20)),
            "buffType": "damage",
            "group": "dmg_burn",
            "p": {"damage_type": "energy"},
            "hasDuration": True,
            "e": 0,
            "time": {"amount": 4.0},
            "loc_name": "burn",
            "loc_desc": "burn",
        },
    }

    # =========================================================================
    # 1. 被动 - 护盾崩解 (ID: 3504): 闪避重击获得 50% 近战增益，近战命中破盾并造成 50% ATK 直伤
    # =========================================================================
    # (1) 获得增益 (橙色图标，无倒计时)
    appr_shield_break = make_statmod_appearance(
        appr_id="appr_breakdown_shield_break_buff",
        callout_text="护盾崩解",
        desc="提升50%近战伤害，近战命中时清除目标所有护盾并施加50%直接伤害",
        pua_icon="\uE807",
        color=AbilityColor.ORANGE_DAMAGE,
        show_callout=True,
    )
    mod_shield_break = {
        "id": "breakdown_shield_break_buff",
        "t": "attack_buff",
        "tm": "",
        "tr": ["onEvade"],
        "uit": ["onEvade"],
        "pri": 0,
        "trm": 0.0,
        "trs": "opponent:level=Heavy",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.50,
        "d": -1.0,  # 无倒计时常驻直至触发
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "attack_buff",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_breakdown_shield_break_buff"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_shield_break)
    validate_appear(appr_shield_break)
    mods["breakdown_shield_break_buff"] = mod_shield_break
    appears["appr_breakdown_shield_break_buff"] = appr_shield_break

    # (2) 近战命中驱散护盾
    m_shatter, a_shatter = make_nullify_statmod(
        mod_id="breakdown_shield_break_nullify",
        target_categories=["armor_up", "shield"],
        max_stacks_per_cat=10,
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Light,Medium,Heavy;self.status=breakdown_shield_break_buff",
        appr_id="appr_breakdown_shatter",
        callout_text="崩解破盾",
        pua_icon="\uE807",
        color_hex=AbilityColor.ORANGE_DAMAGE_TC,
        gradient_bottom=AbilityColor.ORANGE_DAMAGE_GB,
    )
    mods.update(m_shatter)
    appears.update(a_shatter)

    # (3) 近战命中施加 50% 额外直伤
    m_shatter_dmg, a_shatter_dmg = make_direct_dmg_statmod(
        mod_id="breakdown_shield_break_dmg",
        dmg=float(round(base_atk * 0.50)),
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Light,Medium,Heavy;self.status=breakdown_shield_break_buff",
        buff_id="dmg_direct",
    )
    mods.update(m_shatter_dmg)
    appears.update(a_shatter_dmg)

    # (4) 近战命中移除护盾崩解增益
    m_shatter_rm, a_shatter_rm = make_remove_statmod(
        mod_id="breakdown_shield_break_consume",
        target_mod_id="breakdown_shield_break_buff",
        trigger="onHit",
        trigger_scope="level=Light,Medium,Heavy",
        show_callout=False,
    )
    mods.update(m_shatter_rm)
    appears.update(a_shatter_rm)

    # =========================================================================
    # 2. 觉醒技 - 晚期神经质 (ID: 3505): 敌血>50% 获 40% 近战规避；敌血<50% 获 40% 暴击率
    # =========================================================================
    # (1) 敌血 > 50%: 40% 近战规避
    m_paranoia_evade, a_paranoia_evade = make_evade_grant_statmod(
        mod_id="breakdown_paranoia_evade",
        evade_type="melee",
        grant_chance=1.0,
        evade_chance=0.40,
        duration=-1.0,
        trigger="always",
        trigger_scope="opponent:health>0.5",
        appr_id="appr_breakdown_paranoia_evade",
        callout_text="神经质规避",
        pua_icon="\uE509",
        color_hex=AbilityColor.GREEN_HEALTH_TC,
        gradient_bottom=AbilityColor.GREEN_HEALTH_GB,
    )
    mods.update(m_paranoia_evade)
    appears.update(a_paranoia_evade)

    # (2) 规避成功消耗规避增益
    m_paranoia_evade_rm, a_paranoia_evade_rm = make_remove_statmod(
        mod_id="breakdown_paranoia_evade_consume",
        target_mod_id="breakdown_paranoia_evade",
        trigger="onPlayerStateEnter",
        trigger_scope="state=EvadeMelee",
        callout_text="规避",
        pua_icon="\uE509",
        color_hex=AbilityColor.GREEN_HEALTH_TC,
        gradient_bottom=AbilityColor.GREEN_HEALTH_GB,
        show_callout=True,
    )
    mods.update(m_paranoia_evade_rm)
    appears.update(a_paranoia_evade_rm)

    # (3) 敌血 < 50%: 40% 暴击几率
    m_paranoia_crit, a_paranoia_crit = make_crit_rate_statmod(
        mod_id="breakdown_paranoia_crit",
        duration=-1.0,
        crit_bonus=0.40,
        chance=1.0,
        trigger="always",
        trigger_scope="opponent:health<0.5",
        appr_id="appr_breakdown_paranoia_crit",
        callout_text="神经质暴击",
        pua_icon="\uE406",
        color_hex=AbilityColor.YELLOW_STATUS_TC,
        gradient_bottom=AbilityColor.YELLOW_STATUS_GB,
    )
    mods.update(m_paranoia_crit)
    appears.update(a_paranoia_crit)

    # (4) 暴击触发消耗暴击增益
    m_paranoia_crit_rm, a_paranoia_crit_rm = make_remove_statmod(
        mod_id="breakdown_paranoia_crit_consume",
        target_mod_id="breakdown_paranoia_crit",
        trigger="onCrit",
        trigger_scope="",
        show_callout=False,
    )
    mods.update(m_paranoia_crit_rm)
    appears.update(a_paranoia_crit_rm)

    # =========================================================================
    # 3. 特殊技 1 (SP1): 能量流失 (ID: 3506): 50% 概率 5 秒扣除 12% 最大能量 (0.36格)
    # =========================================================================
    m_sp1_leak, a_sp1_leak = make_power_leak_statmod(
        mod_id="breakdown_sp1_power_leak",
        duration=5.0,
        drain_bars=0.36,
        chance=0.50,
        trigger="onSpecial1Hit",
        trigger_scope="isLastHit=true",
        appr_id="appr_breakdown_sp1_leak",
        callout_text="能量流失",
        pua_icon="\uE607",
    )
    mods.update(m_sp1_leak)
    appears.update(a_sp1_leak)

    # =========================================================================
    # 4. 特殊技 3 (SP3): 远程减益 (ID: 3508): 降低对手远程攻击伤害 100%，持续 20 秒
    # =========================================================================
    appr_sp3_ranged = make_statmod_appearance(
        appr_id="appr_breakdown_sp3_ranged_debuff",
        callout_text="远程瘫痪",
        desc="降低对手远程攻击伤害100%，持续20秒",
        pua_icon="\uE519",
        color=AbilityColor.RED_DEBUFF,
        show_callout=True,
    )
    mod_sp3_ranged = {
        "id": "breakdown_sp3_ranged_debuff",
        "t": "attack_buff",
        "tm": "",
        "tr": ["onSpecial3Hit"],
        "uit": ["onSpecial3Hit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": -1.00,  # 降低 100% 伤害
        "d": 20.0,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "ranged_debuff",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_breakdown_sp3_ranged_debuff"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_sp3_ranged)
    validate_appear(appr_sp3_ranged)
    mods["breakdown_sp3_ranged_debuff"] = mod_sp3_ranged
    appears["appr_breakdown_sp3_ranged_debuff"] = appr_sp3_ranged

    # =========================================================================
    # 5. 特殊技 1 (SP1): 暴击几率 (ID: 3512): 最后一击 35% 几率获 30% 暴击率 8 秒
    # =========================================================================
    m_sp1_crit, a_sp1_crit = make_crit_rate_statmod(
        mod_id="breakdown_sp1_crit_rate",
        duration=8.0,
        crit_bonus=0.30,
        chance=0.35,
        trigger="onSpecial1Hit",
        trigger_scope="isLastHit=true",
        appr_id="appr_breakdown_sp1_crit",
        callout_text="暴击几率",
        pua_icon="\uE40D",
    )
    mods.update(m_sp1_crit)
    appears.update(a_sp1_crit)

    # =========================================================================
    # 6. 被动 - 近战规避 (ID: 3513): L4 或 M2 被防时 75% 概率获得 4 秒近战规避
    # =========================================================================
    m_block_evade, a_block_evade = make_evade_grant_statmod(
        mod_id="breakdown_block_evade",
        evade_type="melee",
        grant_chance=0.75,
        evade_chance=1.0,
        duration=4.0,
        trigger="onBlockHit",
        trigger_scope="level=Light4,Medium2",
        appr_id="appr_breakdown_block_evade",
        callout_text="近战规避",
        pua_icon="\uE509",
    )
    mods.update(m_block_evade)
    appears.update(a_block_evade)

    # =========================================================================
    # 7. 特殊技 2 (SP2): 燃烧 (ID: 3514): 最后一击 100% 施加 4 秒燃烧 (120% ATK 火焰伤害)
    # =========================================================================
    m_sp2_burn, a_sp2_burn = make_burn_statmod(
        mod_id="breakdown_sp2_burn",
        duration=4.0,
        total_dmg=float(round(base_atk * 1.20)),
        chance=1.0,
        trigger="onSpecial2Hit",
        trigger_scope="isLastHit=true",
        appr_id="appr_breakdown_sp2_burn",
        callout_text="燃烧",
        pua_icon="\uE41D",
    )
    mods.update(m_sp2_burn)
    appears.update(a_sp2_burn)

    # =========================================================================
    # 8. 特殊技 2 (SP2): 确定性 (ID: 3515): 施加确定性减益，对手下次满气强制释放 SP1
    # =========================================================================
    appr_sp2_certainty = make_statmod_appearance(
        appr_id="appr_breakdown_sp2_certainty",
        callout_text="确定性",
        desc="强制对手下次充满一格能量后立即释放特殊技1",
        pua_icon="\uE909",
        color=AbilityColor.RED_DEBUFF,
        show_callout=True,
    )
    mod_sp2_certainty = {
        "id": "breakdown_sp2_certainty",
        "t": "power_lock",
        "tm": "",
        "tr": ["onSpecial2Hit"],
        "uit": ["onSpecial2Hit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "isLastHit=true",
        "trr": "repeat",
        "c": 1.0,
        "m": 1.0,
        "d": 30.0,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "certainty_debuff",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_breakdown_sp2_certainty"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_sp2_certainty)
    validate_appear(appr_sp2_certainty)
    mods["breakdown_sp2_certainty"] = mod_sp2_certainty
    appears["appr_breakdown_sp2_certainty"] = appr_sp2_certainty

    # =========================================================================
    # 9. 特殊技 3 (SP3): 确定性 (ID: 3516): 施加 2 层确定性减益，对手连续 2 次满气强制释放 SP1
    # =========================================================================
    appr_sp3_certainty = make_statmod_appearance(
        appr_id="appr_breakdown_sp3_certainty",
        callout_text="确定性",
        desc="施加2层确定性，强制对手连续2次满气立即释放特殊技1",
        pua_icon="\uE909",
        color=AbilityColor.RED_DEBUFF,
        show_callout=True,
    )
    mod_sp3_certainty = {
        "id": "breakdown_sp3_certainty",
        "t": "power_lock",
        "tm": "",
        "tr": ["onSpecial3Hit"],
        "uit": ["onSpecial3Hit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 2.0,
        "d": 30.0,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 2,
        "g": "certainty_debuff",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_breakdown_sp3_certainty"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_sp3_certainty)
    validate_appear(appr_sp3_certainty)
    mods["breakdown_sp3_certainty"] = mod_sp3_certainty
    appears["appr_breakdown_sp3_certainty"] = appr_sp3_certainty

    return mods, appears, buffs
