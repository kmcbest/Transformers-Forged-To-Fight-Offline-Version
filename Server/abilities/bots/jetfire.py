#!/usr/bin/env python3
"""
Bot Ability Implementation: 天火 (Jetfire)
=========================================
Bot ID: jetfire_gs_leader2014
阵营: 汽车人 (Autobot) | 职业: 科技系 (Tech)

【官方技能真理源对照 (来自 Upstash KV 实时端点与 TFTF 数据库)】：
-----------------------------------------------------------------------------
1. [被动 - 招架护盾] (ID: 2656, pua_icon: 0xe911)
   - 在最接近状态下对普通远程攻击和远程重击进行格挡会激活招架护盾，
     将该远程攻击以100%的原始攻击力反弹回去。
   - 在最接近状态下对普通近战攻击进行格挡会激活招架护盾，
     本次格挡不产生防御伤害，并且对手会眩晕1秒。

2. [被动 - 能量充能] (ID: 2657, pua_icon: 0xe914)
   - 每次成功招架，获得一个能量充能，最多10层 (紫色图标，无倒计时)。
   - 每层能量充能提升能量功率(Power Rate) 5% (满层10层提升50%)。

3. [被动 - 震击] (ID: 2658, pua_icon: 0xe914)
   - 重击命中时消耗能量充能施加 4s 90% ATK 震击。

4. [觉醒技 - 损害控制] (ID: 2666, pua_icon: 0xe503)
   - 生命值少于75%时，天火的修复系统处于在线状态。此时按住格挡1秒时，消耗一个能量充能，在0.5秒内修复6%的最大生命值。

5. [特殊技 1 - 远程增益] (ID: 2667, pua_icon: 0xe41b)
   - 消耗全部能量充能，得到20秒的远程增益，提升射速20%，每层消耗的能量充能提升远程伤害20%。

6. [特殊技 3 - 能量充能] (ID: 2681, pua_icon: 0xe914)
   - 技能结束后获得3层能量充能。

7. [特殊技 3 - 震击] (ID: 2682, pua_icon: 0xe914)
   - 消耗所有能量充能，转化为同等层数的震击，每层造成攻击力45%的伤害，持续4秒。

8. [特殊技 1 - 能量锁定] (ID: 2683, pua_icon: 0xe523)
   - 如果这次特殊技消耗5个或更多能量充能，则最后一击命中时100%概率触发能量锁定，阻止对方获得能量，持续8秒。

9. [特殊技 2 - 护盾] (ID: 2684, pua_icon: 0xe515)
   - 消耗所有能量充能，得到1个20秒的护盾，每层能量充能减少所有伤害的8%。

10. [特殊技 2 - 修复阻止] (ID: 2685, pua_icon: 0xe90c)
    - 如果这次特殊技消耗5个或更多能量充能，则最后一击命中时100%概率触发修复阻止，阻止对方所有回血能力，持续15秒。
-----------------------------------------------------------------------------
"""

from ..core import (
    make_shock_statmod,
    make_heal_statmod,
    make_ranged_boost_statmod,
    make_power_lock_statmod,
    make_armor_up_statmod,
    validate_color_code,
    validate_statmod,
    validate_appear,
)
from ..registry import register_bot

BOT_ID = "jetfire_gs_leader2014"


@register_bot(BOT_ID, name_zh="天火", desc="经典G1科技系飞行领袖，完美招架反弹护盾、能量充能流转、损害控制自愈、SP1超视距强化与能量锁定、SP2高抗性护盾与禁疗、SP3群震轰炸")
def build_jetfire_abilities(base_hp: float = 28975.0, base_atk: float = 2260.0):
    mods = {}
    appears = {}
    buffs = {}

    # -------------------------------------------------------------------------
    # 1. 被动 - 招架护盾 (ID: 2656): Parry Shield
    # -------------------------------------------------------------------------
    validate_color_code("38BDF8", "parry_shield_tc")
    validate_color_code("0284C7", "parry_shield_gb")
    appr_shield = {
        "id": "appr_jetfire_parry_shield",
        "a": "招架护盾",
        "s": "招架护盾",
        "l": "最接近状态格挡激活护盾，100%反弹远程攻击与重击；近战完全免伤并眩晕对手1秒",
        "ss": "招架护盾",
        "t": "\uE911",
        "f": "",
        "st": "招架护盾",
        "ps": "招架护盾",
        "pl": "招架护盾生效中",
        "tc": "38BDF8",
        "gt": "38BDF8",
        "gb": "0284C7",
    }
    mod_shield = {
        "id": "jetfire_parry_shield",
        "t": "protection",
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
        "g": "parry_shield",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_jetfire_parry_shield"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_shield)
    mods["jetfire_parry_shield"] = mod_shield
    appears["appr_jetfire_parry_shield"] = appr_shield

    # -------------------------------------------------------------------------
    # 2. 被动 - 能量充能 (ID: 2657): Energy Charge
    # -------------------------------------------------------------------------
    validate_color_code("A855F7", "energy_charge_tc")
    validate_color_code("7E22CE", "energy_charge_gb")
    appr_charge = {
        "id": "appr_jetfire_energy_charge",
        "a": "能量充能",
        "s": "能量充能",
        "l": "成功招架获得1层能量充能(上限10层)，每层提升能量功率5%",
        "ss": "能量充能",
        "t": "\uE914",
        "f": "",
        "st": "能量充能",
        "ps": "能量充能",
        "pl": "能量充能生效中",
        "tc": "A855F7",
        "gt": "A855F7",
        "gb": "7E22CE",
    }
    mod_charge = {
        "id": "jetfire_energy_charge",
        "t": "power",
        "tm": "",
        "tr": ["manual"],
        "uit": ["manual"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 1.0,
        "d": -1.0,  # 负数持续时间表示永久/无倒计时堆叠buff (IsIndefinite=true)
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 10,  # 最多 10 层
        "g": "energy_charge",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_jetfire_energy_charge"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_charge)
    mods["jetfire_energy_charge"] = mod_charge
    appears["appr_jetfire_energy_charge"] = appr_charge

    # -------------------------------------------------------------------------
    # 3. 被动 - 震击 (ID: 2658): Shock on Heavy Attack Hit
    # -------------------------------------------------------------------------
    m_shock, a_shock = make_shock_statmod(
        mod_id="jetfire_heavy_shock",
        duration=4.0,
        total_dmg=float(round(base_atk * 0.90)),
        chance=1.0,
        trigger="manual",
        appr_id="appr_jetfire_heavy_shock",
        callout_text="震击",
        show_callout=True,
        pua_icon="\uE914",
        stackable=True,
        target_actor="opponent",
    )
    mods.update(m_shock)
    appears.update(a_shock)

    # -------------------------------------------------------------------------
    # 4. 觉醒技 - 损害控制 (ID: 2666): Damage Control
    # 生命少于 75% 时按住格挡 1 秒，消耗 1 层充能修复 6% HP (0.5s)
    # -------------------------------------------------------------------------
    m_sig_rep, a_sig_rep = make_heal_statmod(
        mod_id="jetfire_sig_repair",
        duration=0.5,
        heal_amount=float(round(base_hp * 0.06)),
        chance=1.0,
        trigger="onPlayerStateEnter",
        trigger_scope="state=Block",
        appr_id="appr_jetfire_sig_repair",
        callout_text="损害控制",
        pua_icon="\uE503",
        color_hex="10B981",
        gradient_bottom="059669",
    )
    mods.update(m_sig_rep)
    appears.update(a_sig_rep)

    # -------------------------------------------------------------------------
    # 5. 特殊技 1 - 远程增益 (ID: 2667)
    # 消耗全部充能，获得 20s 远程增益，射速 +20%，远程伤害 +20%
    # -------------------------------------------------------------------------
    m_sp1_rng, a_sp1_rng = make_ranged_boost_statmod(
        mod_id="jetfire_sp1_ranged_buff",
        duration=20.0,
        damage_bonus=0.20,
        speed_bonus=0.20,
        trigger="onSpecial1Activate",
        appr_id="appr_jetfire_sp1_ranged_buff",
        callout_text="远程增益",
        pua_icon="\uE41B",
        color_hex="FF8800",
        gradient_bottom="D97706",
    )
    mods.update(m_sp1_rng)
    appears.update(a_sp1_rng)

    # -------------------------------------------------------------------------
    # 6. 特殊技 3 - 获得 3 层能量充能 (ID: 2681)
    # -------------------------------------------------------------------------
    mod_sp3_charge = {
        "id": "jetfire_sp3_grant_charge",
        "t": "power",
        "tm": "",
        "tr": ["onSpecial3Activate"],
        "uit": ["onSpecial3Activate"],
        "pri": 0,
        "trm": 0.0,
        "trs": "dmgFlags=LastHit",
        "trr": "repeat",
        "c": 1.0,
        "m": 1.0,
        "d": -1.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 3,
        "g": "energy_charge",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_jetfire_energy_charge"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_sp3_charge)
    mods["jetfire_sp3_grant_charge"] = mod_sp3_charge

    # -------------------------------------------------------------------------
    # 7. 特殊技 3 - 震击 (ID: 2682)
    # 消耗充能转化为震击，每层 45% ATK，持续 4 秒
    # -------------------------------------------------------------------------
    m_sp3_shk, a_sp3_shk = make_shock_statmod(
        mod_id="jetfire_sp3_shock",
        duration=4.0,
        total_dmg=float(round(base_atk * 0.45)),
        chance=1.0,
        trigger="onSpecial3Activate",
        trigger_scope="dmgFlags=LastHit",
        appr_id="appr_jetfire_sp3_shock",
        callout_text="震击",
        pua_icon="\uE914",
        color_hex="EF4444",
        gradient_bottom="B91C1C",
        stackable=True,
    )
    mods.update(m_sp3_shk)
    appears.update(a_sp3_shk)

    # -------------------------------------------------------------------------
    # 8. 特殊技 1 - 能量锁定 8.0s (ID: 2683)
    # 消耗 >=5 充能时触发 8 秒能量锁定
    # -------------------------------------------------------------------------
    m_sp1_lock, a_sp1_lock = make_power_lock_statmod(
        mod_id="jetfire_sp1_power_lock",
        duration=8.0,
        chance=1.0,
        trigger="onSpecial1Hit",
        trigger_scope="dmgFlags=LastHit",
        appr_id="appr_jetfire_sp1_power_lock",
        callout_text="能量锁定",
        pua_icon="\uE523",
        color_hex="EF4444",
        gradient_bottom="B91C1C",
    )
    mods.update(m_sp1_lock)
    appears.update(a_sp1_lock)

    # -------------------------------------------------------------------------
    # 9. 特殊技 2 - 护盾 (ID: 2684)
    # 得到 20 秒护盾，每层减少伤害 8%
    # -------------------------------------------------------------------------
    m_sp2_shd, a_sp2_shd = make_armor_up_statmod(
        mod_id="jetfire_sp2_shield",
        duration=20.0,
        armor_bonus=0.08,
        chance=1.0,
        trigger="onSpecial2Activate",
        appr_id="appr_jetfire_sp2_shield",
        callout_text="护盾",
        pua_icon="\uE515",
        color_hex="29EBF4",
        gradient_bottom="00C5E8",
        stackable=True,
        max_stacks=10,
    )
    mods.update(m_sp2_shd)
    appears.update(a_sp2_shd)

    # -------------------------------------------------------------------------
    # 10. 特殊技 2 - 修复阻止 15.0s (ID: 2685)
    # 消耗 >=5 充能时阻止对方回血 15 秒
    # -------------------------------------------------------------------------
    validate_color_code("EF4444", "heal_block_tc")
    validate_color_code("B91C1C", "heal_block_gb")
    appr_hblock = {
        "id": "appr_jetfire_sp2_heal_block",
        "a": "修复阻止",
        "s": "修复阻止",
        "l": "阻止目标所有回血与自我修复能力",
        "ss": "修复阻止",
        "t": "\uE90C",
        "f": "",
        "st": "修复阻止",
        "ps": "修复阻止",
        "pl": "修复阻止生效中",
        "tc": "EF4444",
        "gt": "EF4444",
        "gb": "B91C1C",
    }
    validate_appear(appr_hblock)
    appears["appr_jetfire_sp2_heal_block"] = appr_hblock

    mod_hblock = {
        "id": "jetfire_sp2_heal_block",
        "t": "heal_block",
        "tm": "",
        "tr": ["onSpecial2Hit"],
        "uit": ["onSpecial2Hit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "dmgFlags=LastHit",
        "trr": "repeat",
        "c": 1.0,
        "m": 1.0,
        "d": 15.0,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "heal_block",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_jetfire_sp2_heal_block"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_hblock)
    mods["jetfire_sp2_heal_block"] = mod_hblock

    return mods, appears, buffs
