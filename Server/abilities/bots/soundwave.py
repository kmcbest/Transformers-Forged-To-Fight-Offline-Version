#!/usr/bin/env python3
"""
Bot Ability Implementation: 声波 (Soundwave)
============================================
Bot ID: soundwave_gs
阵营: 霸天虎 (Decepticon) | 职业: 科技系 (Tech)

【官方技能真理源对照 (来自 tools/new_bots_priority_specs.json)】：
-----------------------------------------------------------------------------
1. [被动 - 震击 / Heavy Shock] (ID: 3395, pua_icon: 0xe914, category: passive)
   - 官方描述: "重击命中100%的概率施加震击，造成攻击50%的伤害，持续6秒。"

2. [被动 - 能量涌动 / Heavy Power Flow] (ID: 3396, pua_icon: 0xe608, category: passive)
   - 官方描述: "声波的普通近战和普通远程攻击不产生能量
重击命中后获得能量涌动增益，每秒产生最大能量的5.7%，直到充满2格能量或者释放特殊技  //重击命中后紫图标出现，无倒计时，充满2格或者放特殊技时图标消失"

3. [特殊技 1 - 眩晕 / SP1 Stun] (ID: 3397, pua_icon: 0xe605, category: sp1)
   - 官方描述: "最后一击命中，60%概率施加眩晕1.5秒。"

4. [特殊技 1 - 能量流失 / SP1 Power Leak] (ID: 3398, pua_icon: 0xe607, category: sp1)
   - 官方描述: "最后一击命中，85%的概率造成能量流失，在4秒内扣除对方1格能量的90%"

5. [特殊技 2 - 震击 / SP2 Shock] (ID: 3399, pua_icon: 0xe914, category: sp2)
   - 官方描述: "最后一击命中，100%的概率施加震击，造成攻击70%的伤害，持续6秒。"

6. [特殊技 3 - 震击 / SP3 Shock] (ID: 3400, pua_icon: 0xe914, category: sp3)
   - 官方描述: "重击命中100%的概率施加震击，造成攻击50%的伤害，持续6秒。"

7. [特殊技 2 - 能量涌动 / SP2 Power Flow] (ID: 3401, pua_icon: 0xe608, category: sp2)
   - 官方描述: "最后一击命中后获得能量涌动增益，每秒产生最大能量的6.7%，直到充满3格能量或者释放特殊技  //最后一击命中后紫图标出现，无倒计时，充满3格或者放特殊技时图标消失"

8. [特殊技 3 - 眩晕 / SP3 Stun] (ID: 3402, pua_icon: 0xe605, category: sp3)
   - 官方描述: "最后一击命中，60%概率施加眩晕1.5秒。"

9. [特殊技 3 - 能量锁定 / SP3 Power Lock] (ID: 3403, pua_icon: 0xe523, category: sp3)
   - 官方描述: "技能完成时70%概率触发能量锁定，阻止对方获得能量，持续8秒"
-----------------------------------------------------------------------------
"""

from ..core import (
    AbilityColor,
    make_shock_statmod,
    make_stun_statmod,
    make_power_leak_statmod,
    make_power_lock_statmod,
    make_statmod_appearance,
    validate_statmod,
    validate_appear,
    validate_color_code,
)
from ..registry import register_bot

BOT_ID = "soundwave_gs"


@register_bot(BOT_ID, name_zh="声波", desc="科技系情报参谋，独特重击共鸣充能机制、高频音波触电与能量流失、强控声波震荡眩晕、SP2超频能量涌动与SP3能量封锁")
def build_soundwave_abilities(base_hp: float = 34850.0, base_atk: float = 3485.0):
    """
    根据基准属性生成声波全部专属能力修饰器。
    基准 5星50级 HP = 34850.0, ATK = 3485.0
    """
    mods = {}
    appears = {}
    buffs = {
        # 声波震击持续能量伤害 (Shock DOT)
        "dmg_shock": {
            "id": "dmg_shock",
            "iconTexture": "",
            "image": "",
            "images3": False,
            "modeAvail": [],
            "scope": "global",
            "valueType": "absolute",
            "displayValue": float(round(base_atk * 0.70)),
            "c": 1,
            "value": float(round(base_atk * 0.70)),
            "buffType": "damage",
            "group": "dmg_shock",
            "p": {"damage_type": "shock"},
            "hasDuration": True,
            "e": 0,
            "time": {"amount": 6.0},
            "loc_name": "shock",
            "loc_desc": "shock",
        },
    }

    # =========================================================================
    # 1. 通用外观 (StatModAppearances)
    # =========================================================================
    # 1.1 重击能量涌动外观 (浅紫色能量图标)
    appr_heavy_power_flow = make_statmod_appearance(
        appr_id="appr_soundwave_heavy_power_flow",
        callout_text="能量涌动",
        desc="重击命中后每秒产生最大能量的5.7%，直到充满2格或释放特殊技",
        pua_icon="\uE608",
        color=AbilityColor.LIGHT_PURPLE_POWER,
        show_callout=True,
    )
    validate_appear(appr_heavy_power_flow)
    appears[appr_heavy_power_flow["id"]] = appr_heavy_power_flow

    # 1.2 SP2 能量涌动外观 (浅紫色能量图标)
    appr_sp2_power_flow = make_statmod_appearance(
        appr_id="appr_soundwave_sp2_power_flow",
        callout_text="能量涌动",
        desc="最后一击命中后每秒产生最大能量的6.7%，直到充满3格或释放特殊技",
        pua_icon="\uE608",
        color=AbilityColor.LIGHT_PURPLE_POWER,
        show_callout=True,
    )
    validate_appear(appr_sp2_power_flow)
    appears[appr_sp2_power_flow["id"]] = appr_sp2_power_flow

    # =========================================================================
    # 2. 被动能力：重击震击与特殊能量涌动 (ID: 3395, 3396)
    # =========================================================================
    # 2.1 重击震击: 造成攻击力 50% 伤害，持续 6 秒 (ID: 3395)
    m_heavy_shock, a_heavy_shock = make_shock_statmod(
        mod_id="soundwave_heavy_shock",
        duration=6.0,
        total_dmg=float(round(base_atk * 0.50)),
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Heavy",
        appr_id="appr_soundwave_shock",
        callout_text="震击",
        pua_icon="\uE914",
    )
    mods.update(m_heavy_shock)
    appears.update(a_heavy_shock)

    # 2.2 声波普通攻击不产生能量 (特性标记)
    mod_no_basic_mana = {
        "id": "soundwave_passive_no_basic_mana",
        "t": "power_gain",
        "tm": "",
        "tr": ["onHit"],
        "uit": ["onHit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "level=Light,Medium,Ranged",
        "trr": "repeat",
        "c": 1.0,
        "m": -1.0,
        "d": 0.0,
        "s": "none",
        "ta": "self",
        "mt": "passive",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "no_basic_mana",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": [],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_no_basic_mana)
    mods[mod_no_basic_mana["id"]] = mod_no_basic_mana

    # 2.3 重击命中获得能量涌动: 每秒产生 5.7% 最大能量 (51.3 Mana/s) (ID: 3396)
    mod_heavy_power_flow = {
        "id": "soundwave_heavy_power_flow",
        "t": "power_gain",
        "tm": "",
        "tr": ["onHit"],
        "uit": ["onHit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "level=Heavy",
        "trr": "repeat",
        "c": 1.0,
        "m": 51.3,
        "d": 12.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "power_flow",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_soundwave_heavy_power_flow"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_heavy_power_flow)
    mods[mod_heavy_power_flow["id"]] = mod_heavy_power_flow

    # =========================================================================
    # 3. 特殊技 1 (SP1): 眩晕与能量流失 (ID: 3397, 3398)
    # =========================================================================
    # 3.1 SP1 最后一击眩晕: 60%概率持续 1.5 秒 (ID: 3397)
    m_sp1_stun, a_sp1_stun = make_stun_statmod(
        mod_id="soundwave_sp1_stun",
        duration=1.5,
        chance=0.60,
        trigger="onSpecial1Hit",
        trigger_scope="dmgFlags=LastHit",
        appr_id="appr_soundwave_stun",
        callout_text="眩晕",
        pua_icon="\uE605",
    )
    mods.update(m_sp1_stun)
    appears.update(a_sp1_stun)

    # 3.2 SP1 最后一击能量流失: 85%概率4秒扣除1格能量的90% (0.90 bars) (ID: 3398)
    m_sp1_leak, a_sp1_leak = make_power_leak_statmod(
        mod_id="soundwave_sp1_power_leak",
        duration=4.0,
        drain_bars=0.90,
        chance=0.85,
        trigger="onSpecial1Hit",
        trigger_scope="dmgFlags=LastHit",
        appr_id="appr_soundwave_power_leak",
        callout_text="能量流失",
        pua_icon="\uE607",
    )
    mods.update(m_sp1_leak)
    appears.update(a_sp1_leak)

    # =========================================================================
    # 4. 特殊技 2 (SP2): 震击与能量涌动 (ID: 3399, 3401)
    # =========================================================================
    # 4.1 SP2 最后一击震击: 100%概率造成攻击力 70% 伤害，持续 6 秒 (ID: 3399)
    m_sp2_shock, a_sp2_shock = make_shock_statmod(
        mod_id="soundwave_sp2_shock",
        duration=6.0,
        total_dmg=float(round(base_atk * 0.70)),
        chance=1.0,
        trigger="onSpecial2Hit",
        trigger_scope="dmgFlags=LastHit",
        appr_id="appr_soundwave_shock",
        callout_text="震击",
        pua_icon="\uE914",
    )
    mods.update(m_sp2_shock)
    appears.update(a_sp2_shock)

    # 4.2 SP2 最后一击获得能量涌动: 每秒产生 6.7% 最大能量 (60.3 Mana/s) (ID: 3401)
    mod_sp2_power_flow = {
        "id": "soundwave_sp2_power_flow",
        "t": "power_gain",
        "tm": "",
        "tr": ["onSpecial2Hit"],
        "uit": ["onSpecial2Hit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "dmgFlags=LastHit",
        "trr": "repeat",
        "c": 1.0,
        "m": 60.3,
        "d": 15.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "power_flow",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_soundwave_sp2_power_flow"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_sp2_power_flow)
    mods[mod_sp2_power_flow["id"]] = mod_sp2_power_flow

    # =========================================================================
    # 5. 特殊技 3 (SP3): 震击、眩晕与能量锁定 (ID: 3400, 3402, 3403)
    # =========================================================================
    # 5.1 SP3 震击: 100%概率造成攻击力 50% 伤害，持续 6 秒 (ID: 3400)
    m_sp3_shock, a_sp3_shock = make_shock_statmod(
        mod_id="soundwave_sp3_shock",
        duration=6.0,
        total_dmg=float(round(base_atk * 0.50)),
        chance=1.0,
        trigger="onSpecial3Hit",
        trigger_scope="dmgFlags=LastHit",
        appr_id="appr_soundwave_shock",
        callout_text="震击",
        pua_icon="\uE914",
    )
    mods.update(m_sp3_shock)
    appears.update(a_sp3_shock)

    # 5.2 SP3 最后一击眩晕: 60%概率持续 1.5 秒 (ID: 3402)
    m_sp3_stun, a_sp3_stun = make_stun_statmod(
        mod_id="soundwave_sp3_stun",
        duration=1.5,
        chance=0.60,
        trigger="onSpecial3Hit",
        trigger_scope="dmgFlags=LastHit",
        appr_id="appr_soundwave_stun",
        callout_text="眩晕",
        pua_icon="\uE605",
    )
    mods.update(m_sp3_stun)
    appears.update(a_sp3_stun)

    # 5.3 SP3 能量锁定: 70%概率触发能量锁定持续 8 秒 (ID: 3403)
    m_sp3_lock, a_sp3_lock = make_power_lock_statmod(
        mod_id="soundwave_sp3_power_lock",
        duration=8.0,
        chance=0.70,
        trigger="onSpecial3Hit",
        trigger_scope="dmgFlags=LastHit",
        appr_id="appr_soundwave_power_lock",
        callout_text="能量锁定",
        pua_icon="\uE523",
    )
    mods.update(m_sp3_lock)
    appears.update(a_sp3_lock)

    return mods, appears, buffs
