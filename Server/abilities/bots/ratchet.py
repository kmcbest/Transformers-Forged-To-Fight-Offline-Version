#!/usr/bin/env python3
"""
Bot Ability Implementation: 救护车 (Ratchet)
===========================================
Bot ID: ratchet_gs_kabam
阵营: 汽车人 (Autobot) | 职业: 科技系 (Tech)

【官方技能真理源对照 (来自 Upstash KV 聚合 Priorities 清单)】：
-----------------------------------------------------------------------------
1. [被动 - 自我诊断] (ID: 2753, pua_icon: 0xe60e)
   - 当救护车血量低于50%时，完成重击动作时会激活自我诊断，修复10%的生命值，并获得最大能量槽20%的能量，持续10秒。
2. [SP1 - 冲击扳手] (ID: 2756, pua_icon: 0xe605)
   - 40%的概率眩晕对手2.5秒，对手身上的每层震击增加20%的概率。
3. [SP2 - 能量获取] (ID: 2757, pua_icon: 0xe606)
   - 根据损失的生命值，最多获取最大能量槽的28.8% (50%血量时获取14.4%)。
4. [SP2 - 回血] (ID: 2767, pua_icon: 0xe503)
   - 立即修复受到伤害的17% (已损失血量的17%)。
-----------------------------------------------------------------------------
"""

from ..core import (
    make_heal_statmod,
    make_shock_statmod,
    make_stun_statmod,
    validate_color_code,
    validate_statmod,
)
from ..registry import register_bot

BOT_ID = "ratchet_gs_kabam"


@register_bot(BOT_ID, name_zh="救护车", desc="科技系战地医师，濒危重击自我诊断回血回能，SP1扳手眩晕控制，SP2依已损血量紧急充能与自我修复")
def build_ratchet_abilities(base_hp: float = 28352.0, base_atk: float = 2029.0):
    mods = {}
    appears = {}

    # 1. 被动自我诊断 (ID: 2753): HP < 50% 时重击完成修复 10% HP 并获 20% 能量 10s
    diag_heal_amount = float(round(base_hp * 0.10, 2))
    m_diag, a_diag = make_heal_statmod(
        mod_id="ratchet_self_diagnosis",
        duration=10.0,
        heal_amount=diag_heal_amount,
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Heavy;isLastHit=true",
        appr_id="appr_ratchet_self_diagnosis",
        callout_text="自我诊断",
        pua_icon="\uE60E",
    )
    mods.update(m_diag)
    appears.update(a_diag)

    # 自我诊断附带 10s 获得 20% 能量
    appr_diag_pwr = {
        "id": "appr_ratchet_self_diag_pwr",
        "a": "自我诊断回能",
        "s": "能量获取",
        "l": "自我诊断激活期间持续获取最大能量槽的20%",
        "ss": "持续回能20%",
        "t": "\uE606",
        "f": "",
        "st": "",
        "ps": "自我诊断",
        "pl": "自我诊断能量获取中",
        "tc": "3B82F6",
        "gt": "3B82F6",
        "gb": "1D4ED8",
    }
    mod_diag_pwr = {
        "id": "ratchet_self_diag_pwr",
        "t": "power_gain",
        "tm": "",
        "tr": ["onHit"],
        "uit": [],
        "pri": 0,
        "trm": 0.0,
        "trs": "level=Heavy;isLastHit=true",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.20,
        "d": 10.0,
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
        "a": ["appr_ratchet_self_diag_pwr"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_diag_pwr)
    mods["ratchet_self_diag_pwr"] = mod_diag_pwr
    appears["appr_ratchet_self_diag_pwr"] = appr_diag_pwr

    # 2. SP1 冲击扳手眩晕 (ID: 2756): 40% 几率眩晕 2.5 秒
    m_stun, a_stun = make_stun_statmod(
        mod_id="ratchet_sp1_wrench_stun",
        duration=2.5,
        chance=0.40,
        trigger="onSpecial1Activate",
        appr_id="appr_ratchet_sp1_wrench_stun",
        callout_text="眩晕",
        pua_icon="\uE605",
    )
    mods.update(m_stun)
    appears.update(a_stun)

    # 3. SP2 能量获取 (ID: 2757): 依据损失血量最多获取 28.8% 最大能量
    validate_color_code("3B82F6", "ratchet_pwr_tc")
    validate_color_code("1D4ED8", "ratchet_pwr_gb")
    appr_pwr = {
        "id": "appr_ratchet_sp2_power_gain",
        "a": "能量虹吸",
        "s": "能量获取",
        "l": "依据损失血量动态获取最大能量槽的28.8%",
        "ss": "损血动态回能",
        "t": "\uE606",
        "f": "",
        "st": "能量获取",
        "ps": "能量虹吸",
        "pl": "能量虹吸生效中",
        "tc": "3B82F6",
        "gt": "3B82F6",
        "gb": "1D4ED8",
    }
    mod_pwr = {
        "id": "ratchet_sp2_power_gain",
        "t": "buff",
        "tm": "",
        "tr": ["onSpecial2Activate"],
        "uit": ["onSpecial2Activate"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.288,
        "d": 0.0,
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
        "a": ["appr_ratchet_sp2_power_gain"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_pwr)
    mods["ratchet_sp2_power_gain"] = mod_pwr
    appears["appr_ratchet_sp2_power_gain"] = appr_pwr

    # 4. SP2 回血 (ID: 2767): 立即修复已损伤害的 17% (基准 17% HP: 28352 * 0.17 = 4820)
    rep_heal_amount = float(round(base_hp * 0.17, 2))
    m_rep, a_rep = make_heal_statmod(
        mod_id="ratchet_sp2_repair",
        duration=0.0,
        heal_amount=rep_heal_amount,
        chance=1.0,
        trigger="onSpecial2Activate",
        trigger_scope="",
        appr_id="appr_ratchet_sp2_repair",
        callout_text="战地修复",
        pua_icon="\uE503",
    )
    mods.update(m_rep)
    appears.update(a_rep)


# 5. [既有技能保留] 战时远程暴击震击 (6.5s, 75% ATK)
    m_rb_shock, a_rb_shock = make_shock_statmod(
        mod_id="ratchet_ranged_shock",
        duration=6.5,
        total_dmg=float(round(base_atk * 0.75)),
        chance=1.0,
        trigger="onCrit",
        trigger_scope="level=Ranged",
        appr_id="appr_ratchet_ranged_shock",
        callout_text="震击",
        pua_icon="\uE914",
        color_hex="FF0000",
        gradient_bottom="FF0000",
    )
    mods.update(m_rb_shock)
    appears.update(a_rb_shock)

    # 6. [既有技能保留] SP3 诊断扫描震击 (4.0s, 97.5% ATK)
    m_sp3_shock, a_sp3_shock = make_shock_statmod(
        mod_id="ratchet_sp3_shock",
        duration=4.0,
        total_dmg=float(round(base_atk * 0.975)),
        chance=1.0,
        trigger="onSpecial3Hit",
        trigger_scope="",
        appr_id="appr_ratchet_sp3_shock",
        callout_text="震击",
        pua_icon="\uE914",
        color_hex="FF0000",
        gradient_bottom="FF0000",
    )
    mods.update(m_sp3_shock)
    appears.update(a_sp3_shock)

    return mods, appears

