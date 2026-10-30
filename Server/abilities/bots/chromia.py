#!/usr/bin/env python3
"""
Bot Ability Implementation: 克劳莉娅 (Chromia)
=============================================
Bot ID: chromia_gs_kabam
阵营: 汽车人 (Autobot) | 职业: 侦察兵 (Scout)

【官方技能真理源对照 (来自 character_abilities 数据库与在线优先实现)】：
-----------------------------------------------------------------------------
1. [被动 - 减速 / Deceleration] (ID: 2486, pua_icon: E952)
   - 官方描述: "远程攻击命中或被防御时，有60%的概率施加减速，持续3.2秒，可叠加
     每层减速降低对手能量功率10%
     减速中的对手绝对不触发规避"
   - 实现方案:
     a) chromia_ranged_decel: 远程命中或被防御 60% 几率施加 3.2 秒减速，可叠加 10 层，降低对手 10% 能量功率并压制规避。

2. [SP1 - 流血 / Bleed] (ID: 2487, pua_icon: 0xe401)
   - 官方描述: "100%几率触发流血，造成攻击力69.3%的伤害，持续4秒。"
   - 实现方案:
     b) chromia_sp1_bleed: SP1 命中 100% 触发 4 秒流血，造成 69.3% ATK 物理流血伤害。

3. [SP2 - 流血 / Bleed] (ID: 2488, pua_icon: 0xe401)
   - 官方描述: "100%几率触发流血，造成攻击力100%的伤害，持续4秒。"
   - 实现方案:
     c) chromia_sp2_bleed: SP2 命中 100% 触发 4 秒流血，造成 100% ATK 物理流血伤害。

4. [SP2 - 减速 / Deceleration] (ID: 2489, pua_icon: E952)
   - 官方描述: "施加减速，持续9秒，可叠加
     每层减速降低对手能量功率10%
     减速中的对手绝对不触发规避"
   - 实现方案:
     d) chromia_sp2_decel: SP2 命中施加 9 秒减速，降低 10% 能量功率并禁止对手规避。

5. [SP3 - 减速 / Deceleration] (ID: 2490, pua_icon: E952)
   - 官方描述: "施加减速，持续23.6秒，可叠加
     每层减速降低对手能量功率10%
     减速中的对手绝对不触发规避"
   - 实现方案:
     e) chromia_sp3_decel: SP3 命中施加 23.6 秒长效减速，降低 10% 能量功率并禁止对手规避。

6. [SP3 - 流血 / Bleed] (ID: 2491, pua_icon: 0xe401)
   - 官方描述: "100%几率触发流血，造成攻击力200%的伤害，持续25秒。"
   - 实现方案:
     f) chromia_sp3_bleed: SP3 命中 100% 施加 25 秒极速撕裂流血，造成 200% ATK 巨额流血伤害。

7. [觉醒技 - 瞄准目标 / Eyes on Target] (ID: 2481, pua_icon: E608)
   - 官方描述: "所有特殊技最后一击：得到能量涌动增益，提升能量获得功率120%，持续7秒。"
   - 实现方案:
     g) chromia_sig_power_surge: 任意特殊技最后一击命中获得能量涌动，提升能量获取功率 120%，持续 7 秒。

8. [觉醒技 - 规避 / Evade] (ID: 2492, pua_icon: 0xe518)
   - 官方描述: "所有特殊技最后一击：获得规避增益，30%的概率规避敌人远程攻击，持续7秒"
   - 实现方案:
     h) chromia_sig_evade: 任意特殊技最后一击命中获得远程规避增益，30% 概率规避敌人远程攻击，持续 7 秒。

9. [觉醒技 - 顶光区的炸弹 / Acrolight Bomb] (ID: 2493, pua_icon: E40E)
   - 官方描述: "所有特殊技：技能命中后最后一击施加炸弹减益，持续5秒  // 灰色图标
     5秒内未被对手击中，炸弹造成攻击力100%的即时伤害，并眩晕2.5秒"
   - 实现方案:
     i) chromia_acrolight_bomb: 所有特殊技最后一击施加 5 秒延时炸弹减益 (灰色图标)。
     j) chromia_bomb_direct_dmg: 炸弹 5 秒未被引爆即结算 100% ATK 即时直接伤害。
     k) chromia_bomb_stun: 炸弹引爆同时施加 2.5 秒眩晕硬控。
-----------------------------------------------------------------------------
"""

from typing import Dict, Any, Tuple
from ..core import (
    AbilityColor,
    make_bleed_statmod,
    make_stun_statmod,
    make_evade_grant_statmod,
    make_direct_dmg_statmod,
    make_statmod_appearance,
    validate_statmod,
    validate_appear,
)
from ..registry import register_bot

BOT_ID = "chromia_gs_kabam"


@register_bot(
    BOT_ID,
    name_zh="克劳莉娅",
    desc="汽车人神枪突击手，远程多段射击施加减速阻遏规避，全段特殊技高额流血，觉醒瞄准目标能量涌动、远程规避与顶光区定时炸弹毁灭眩晕",
)
def build_chromia_abilities(
    base_hp: float = 34850.0,
    base_atk: float = 3485.0,
) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """
    根据基准属性生成克劳莉娅 (Chromia) 全部专属能力修饰器。
    基准 5星50级 HP = 34850.0, ATK = 3485.0
    """
    mods = {}
    appears = {}
    buffs = {
        # 克劳莉娅流血伤害模板
        "dmg_bleed": {
            "id": "dmg_bleed",
            "iconTexture": "",
            "image": "",
            "images3": False,
            "modeAvail": [],
            "scope": "global",
            "valueType": "absolute",
            "displayValue": float(round(base_atk * 0.693)),
            "c": 1,
            "value": float(round(base_atk * 0.693)),
            "buffType": "damage",
            "group": "dmg_bleed",
            "p": {"damage_type": "bleed"},
            "hasDuration": True,
            "e": 0,
            "time": {"amount": 4.0},
            "loc_name": "bleed",
            "loc_desc": "bleed",
        },
        # 顶光区炸弹即时直接伤害
        "dmg_direct": {
            "id": "dmg_direct",
            "iconTexture": "",
            "image": "",
            "images3": False,
            "modeAvail": [],
            "scope": "global",
            "valueType": "absolute",
            "displayValue": float(round(base_atk * 1.00)),
            "c": 1,
            "value": float(round(base_atk * 1.00)),
            "buffType": "damage",
            "group": "dmg_direct",
            "p": {"damage_type": "energy"},
            "hasDuration": True,
            "e": 0,
            "time": {"amount": 0.5},
            "loc_name": "bomb_direct",
            "loc_desc": "bomb_direct",
        },
    }

    # =========================================================================
    # 1. 被动 - 减速 (ID: 2486): 远程攻击命中或被防 60% 施加 3.2 秒减速，-10% 能量功率且禁止规避
    # =========================================================================
    appr_passive_decel = make_statmod_appearance(
        appr_id="appr_chromia_passive_decel",
        callout_text="减速",
        desc="降低能量获取功率10%，且期间目标无法触发规避(持续3.2秒)",
        pua_icon="\uE952",
        color=AbilityColor.RED_DEBUFF,
        show_callout=True,
    )
    mod_passive_decel = {
        "id": "chromia_ranged_decel",
        "t": "power_rate_debuff",
        "tm": "",
        "tr": ["onHit", "onBlockHit"],
        "uit": ["onHit", "onBlockHit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "level=Ranged",
        "trr": "repeat",
        "c": 0.60,
        "m": -0.10,
        "d": 3.2,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 10,
        "g": "deceleration_debuff",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_chromia_passive_decel"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
        "suppress_evade": True,
    }
    validate_statmod(mod_passive_decel)
    validate_appear(appr_passive_decel)
    mods["chromia_ranged_decel"] = mod_passive_decel
    appears["appr_chromia_passive_decel"] = appr_passive_decel

    # =========================================================================
    # 2. 特殊技 1 (SP1): 流血 (ID: 2487): 100% 触发 4 秒流血 (69.3% ATK)
    # =========================================================================
    m_sp1_bleed, a_sp1_bleed = make_bleed_statmod(
        mod_id="chromia_sp1_bleed",
        duration=4.0,
        total_dmg=float(round(base_atk * 0.693)),
        chance=1.0,
        trigger="onSpecial1Hit",
        trigger_scope="",
        appr_id="appr_chromia_sp1_bleed",
        callout_text="流血",
        pua_icon="\uE401",
        buff_id="dmg_bleed",
    )
    mods.update(m_sp1_bleed)
    appears.update(a_sp1_bleed)

    # =========================================================================
    # 3. 特殊技 2 (SP2): 流血 (ID: 2488): 100% 触发 4 秒流血 (100% ATK)
    # =========================================================================
    m_sp2_bleed, a_sp2_bleed = make_bleed_statmod(
        mod_id="chromia_sp2_bleed",
        duration=4.0,
        total_dmg=float(round(base_atk * 1.00)),
        chance=1.0,
        trigger="onSpecial2Hit",
        trigger_scope="",
        appr_id="appr_chromia_sp2_bleed",
        callout_text="流血",
        pua_icon="\uE401",
        buff_id="dmg_bleed",
    )
    mods.update(m_sp2_bleed)
    appears.update(a_sp2_bleed)

    # =========================================================================
    # 4. 特殊技 2 (SP2): 减速 (ID: 2489): 施加 9 秒减速，-10% 能量功率且禁止规避
    # =========================================================================
    appr_sp2_decel = make_statmod_appearance(
        appr_id="appr_chromia_sp2_decel",
        callout_text="减速",
        desc="降低能量获取功率10%，且期间目标无法触发规避(持续9秒)",
        pua_icon="\uE952",
        color=AbilityColor.RED_DEBUFF,
        show_callout=True,
    )
    mod_sp2_decel = {
        "id": "chromia_sp2_decel",
        "t": "power_rate_debuff",
        "tm": "",
        "tr": ["onSpecial2Hit"],
        "uit": ["onSpecial2Hit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": -0.10,
        "d": 9.0,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 10,
        "g": "deceleration_debuff",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_chromia_sp2_decel"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
        "suppress_evade": True,
    }
    validate_statmod(mod_sp2_decel)
    validate_appear(appr_sp2_decel)
    mods["chromia_sp2_decel"] = mod_sp2_decel
    appears["appr_chromia_sp2_decel"] = appr_sp2_decel

    # =========================================================================
    # 5. 特殊技 3 (SP3): 减速 (ID: 2490): 施加 23.6 秒减速，-10% 能量功率且禁止规避
    # =========================================================================
    appr_sp3_decel = make_statmod_appearance(
        appr_id="appr_chromia_sp3_decel",
        callout_text="减速",
        desc="降低能量获取功率10%，且期间目标无法触发规避(持续23.6秒)",
        pua_icon="\uE952",
        color=AbilityColor.RED_DEBUFF,
        show_callout=True,
    )
    mod_sp3_decel = {
        "id": "chromia_sp3_decel",
        "t": "power_rate_debuff",
        "tm": "",
        "tr": ["onSpecial3Hit"],
        "uit": ["onSpecial3Hit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": -0.10,
        "d": 23.6,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 10,
        "g": "deceleration_debuff",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_chromia_sp3_decel"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
        "suppress_evade": True,
    }
    validate_statmod(mod_sp3_decel)
    validate_appear(appr_sp3_decel)
    mods["chromia_sp3_decel"] = mod_sp3_decel
    appears["appr_chromia_sp3_decel"] = appr_sp3_decel

    # =========================================================================
    # 6. 特殊技 3 (SP3): 流血 (ID: 2491): 100% 触发 25 秒极速撕裂流血 (200% ATK)
    # =========================================================================
    m_sp3_bleed, a_sp3_bleed = make_bleed_statmod(
        mod_id="chromia_sp3_bleed",
        duration=25.0,
        total_dmg=float(round(base_atk * 2.00)),
        chance=1.0,
        trigger="onSpecial3Hit",
        trigger_scope="",
        appr_id="appr_chromia_sp3_bleed",
        callout_text="流血",
        pua_icon="\uE401",
        buff_id="dmg_bleed",
    )
    mods.update(m_sp3_bleed)
    appears.update(a_sp3_bleed)

    # =========================================================================
    # 7. 觉醒技 - 瞄准目标 (ID: 2481): 所有特殊技最后一击获得能量涌动(+120%功率,持续7秒)
    # =========================================================================
    appr_sig_surge = make_statmod_appearance(
        appr_id="appr_chromia_sig_eyes_on_target",
        callout_text="能量涌动",
        desc="特殊技瞄准锁定目标，提升能量获取功率120%，持续7秒",
        pua_icon="\uE608",
        color=AbilityColor.LIGHT_PURPLE_POWER,
        show_callout=True,
    )
    mod_sig_surge = {
        "id": "chromia_sig_power_surge",
        "t": "power_rate_buff",
        "tm": "",
        "tr": ["onSpecial1Hit", "onSpecial2Hit", "onSpecial3Hit"],
        "uit": ["onSpecial1Hit", "onSpecial2Hit", "onSpecial3Hit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "isLastHit=true",
        "trr": "repeat",
        "c": 1.0,
        "m": 1.20,
        "d": 7.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "power_surge_buff",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_chromia_sig_eyes_on_target"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_sig_surge)
    validate_appear(appr_sig_surge)
    mods["chromia_sig_power_surge"] = mod_sig_surge
    appears["appr_chromia_sig_eyes_on_target"] = appr_sig_surge

    # =========================================================================
    # 8. 觉醒技 - 规避 (ID: 2492): 所有特殊技最后一击获得远程规避增益(30%概率,持续7秒)
    # =========================================================================
    m_sig_evade, a_sig_evade = make_evade_grant_statmod(
        mod_id="chromia_sig_evade",
        evade_type="ranged",
        grant_chance=1.0,
        evade_chance=0.30,
        duration=7.0,
        trigger="onSpecial1Hit",
        trigger_scope="isLastHit=true",
        appr_id="appr_chromia_sig_evade",
        callout_text="远程规避",
        pua_icon="\uE518",
    )
    # 补充 SP2 与 SP3 触发列表
    m_sig_evade["chromia_sig_evade"]["tr"] = ["onSpecial1Hit", "onSpecial2Hit", "onSpecial3Hit"]
    m_sig_evade["chromia_sig_evade"]["uit"] = ["onSpecial1Hit", "onSpecial2Hit", "onSpecial3Hit"]
    mods.update(m_sig_evade)
    appears.update(a_sig_evade)

    # =========================================================================
    # 9. 觉醒技 - 顶光区的炸弹 (ID: 2493): 特殊技最后一击施加 5 秒炸弹减益，引爆造成 100% ATK 直伤 + 2.5 秒眩晕
    # =========================================================================
    # (1) 顶光区炸弹 5 秒延时减益 (灰色图标 E40E)
    appr_bomb = make_statmod_appearance(
        appr_id="appr_chromia_acrolight_bomb",
        callout_text="顶光区炸弹",
        desc="附着顶光区定时炸弹，5秒倒计时结束引爆造成100%攻击力直接伤害并眩晕2.5秒",
        pua_icon="\uE40E",
        color=AbilityColor.GRAY_COOLDOWN,
        show_callout=True,
    )
    mod_bomb = {
        "id": "chromia_acrolight_bomb",
        "t": "acrolight_bomb",
        "tm": "",
        "tr": ["onSpecial1Hit", "onSpecial2Hit", "onSpecial3Hit"],
        "uit": ["onSpecial1Hit", "onSpecial2Hit", "onSpecial3Hit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "isLastHit=true",
        "trr": "repeat",
        "c": 1.0,
        "m": 1.0,
        "d": 5.0,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "acrolight_bomb_debuff",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_chromia_acrolight_bomb"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_bomb)
    validate_appear(appr_bomb)
    mods["chromia_acrolight_bomb"] = mod_bomb
    appears["appr_chromia_acrolight_bomb"] = appr_bomb

    # (2) 炸弹引爆 100% 攻击力直接伤害
    m_bomb_dmg, a_bomb_dmg = make_direct_dmg_statmod(
        mod_id="chromia_bomb_direct_dmg",
        dmg=float(round(base_atk * 1.00)),
        chance=1.0,
        trigger="onStatModExpire",
        trigger_scope="mod=chromia_acrolight_bomb",
        buff_id="dmg_direct",
    )
    mods.update(m_bomb_dmg)
    appears.update(a_bomb_dmg)

    # (3) 炸弹引爆 2.5 秒眩晕
    m_bomb_stun, a_bomb_stun = make_stun_statmod(
        mod_id="chromia_bomb_stun",
        duration=2.5,
        chance=1.0,
        trigger="onStatModExpire",
        trigger_scope="mod=chromia_acrolight_bomb",
        appr_id="appr_chromia_bomb_stun",
        callout_text="眩晕",
        pua_icon="\uE605",
    )
    mods.update(m_bomb_stun)
    appears.update(a_bomb_stun)

    return mods, appears, buffs
