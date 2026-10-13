#!/usr/bin/env python3
"""
Bot Ability Implementation: 猩猩队长 / 原始擎天柱 (Optimus Primal)
=================================================================
Bot ID: optimusprimal_bw_mp32
阵营: 巨无霸 (Maximal) | 职业: 格斗系 (Brawler)

【官方技能真理源对照 (来自 Upstash KV 聚合 Priorities 清单)】：
-----------------------------------------------------------------------------
1. [被动 - 护甲增益] (ID: 2709, pua_icon: 0xe517)
   - 当受到攻击时，有20%的概率获得护甲增益，降低受到攻击伤害的4%，无倒计时，最大堆叠10层。
2. [被动 - 近战增益] (ID: 2710, pua_icon: 0xe412)
   - 格挡近战攻击时有30%的概率得到一层18%的近战增益，持续6秒。
3. [被动 - 增益转换] (ID: 2711, pua_icon: 0xe412)
   - 发动重击时，将所有护甲增益转化为近战增益，每一层增加18%的近战伤害，持续6秒。
4. [SP3 - 攻击减益] (ID: 2713, pua_icon: 0xe916)
   - 100%的概率施加攻击减益，降低对手攻击力20%，持续32秒。
-----------------------------------------------------------------------------
"""

from ..core import (
    make_attack_boost_statmod,
    make_armor_up_statmod,
    validate_color_code,
    validate_statmod,
)
from ..registry import register_bot

BOT_ID = "optimusprimal_bw_mp32"


@register_bot(BOT_ID, name_zh="猩猩队长", desc="巨无霸最高领袖，受创叠加上限10层永久护甲，格挡近战反击增益，重击瞬间全护甲转近战增益")
def build_optimusprimal_abilities(base_hp: float = 33000.0, base_atk: float = 2200.0):
    mods = {}
    appears = {}

    # 1. 被动护甲增益 (ID: 2709): 受击 20% 获 4% 护甲，无倒计时，上限 10 层
    m_arm, a_arm = make_armor_up_statmod(
        mod_id="optimusprimal_passive_armor_up",
        duration=0.0,
        armor_bonus=0.04,
        chance=0.20,
        trigger="onPreDamage",
        appr_id="appr_optimusprimal_passive_armor_up",
        callout_text="护甲",
        show_callout=True,
        pua_icon="\uE517",
        stackable=True,
        max_stacks=10,
    )
    mods.update(m_arm)
    appears.update(a_arm)

    # 2. 格挡近战增益 (ID: 2710): 格挡近战 30% 获 18% 近战增益 6s
    m_blk, a_blk = make_attack_boost_statmod(
        mod_id="optimusprimal_block_melee_buff",
        duration=6.0,
        attack_bonus=0.18,
        chance=0.30,
        trigger="onPlayerStateEnter",
        trigger_scope="state=Block",
        appr_id="appr_optimusprimal_block_melee_buff",
        callout_text="近战增益",
        show_callout=True,
        pua_icon="\uE412",
    )
    mods.update(m_blk)
    appears.update(a_blk)

    # 3. 增益转换 (ID: 2711): 重击将所有护甲转化为近战增益 (每层 18% 持续 6s)
    validate_color_code("F59E0B", "primal_convert_tc")
    validate_color_code("D97706", "primal_convert_gb")
    appr_conv = {
        "id": "appr_optimusprimal_armor_to_melee",
        "a": "野兽狂怒",
        "s": "增益转换",
        "l": "重击发起将所有护甲层数转化为近战增益",
        "ss": "护甲转近战增益",
        "t": "\uE412",
        "f": "",
        "st": "增益转换",
        "ps": "野兽狂怒",
        "pl": "野兽狂怒生效中",
        "tc": "F59E0B",
        "gt": "F59E0B",
        "gb": "D97706",
    }
    mod_conv = {
        "id": "optimusprimal_armor_to_melee",
        "t": "passive",
        "tm": "",
        "tr": ["onPlayerStateEnter"],
        "uit": ["onPlayerStateEnter"],
        "pri": 0,
        "trm": 0.0,
        "trs": "state=HeavyCharge",
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
        "g": "buff_convert",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_optimusprimal_armor_to_melee"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_conv)
    mods["optimusprimal_armor_to_melee"] = mod_conv
    appears["appr_optimusprimal_armor_to_melee"] = appr_conv

    # 4. SP3 攻击减益 (ID: 2713): 100% 施加 20% 攻击减益 32s
    validate_color_code("EF4444", "primal_sp3_tc")
    validate_color_code("B91C1C", "primal_sp3_gb")
    appr_sp3 = {
        "id": "appr_optimusprimal_sp3_atk_debuff",
        "a": "咆哮压制",
        "s": "攻击减益",
        "l": "降低对手20%攻击力持续32秒",
        "ss": "攻击弱化",
        "t": "\uE916",
        "f": "",
        "st": "攻击减益",
        "ps": "咆哮压制",
        "pl": "咆哮压制生效中",
        "tc": "EF4444",
        "gt": "EF4444",
        "gb": "B91C1C",
    }
    mod_sp3 = {
        "id": "optimusprimal_sp3_atk_debuff",
        "t": "attack_debuff",
        "tm": "",
        "tr": ["onSpecial3Activate"],
        "uit": ["onSpecial3Activate"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.20,
        "d": 32.0,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "attack_debuff",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_optimusprimal_sp3_atk_debuff"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_sp3)
    mods["optimusprimal_sp3_atk_debuff"] = mod_sp3
    appears["appr_optimusprimal_sp3_atk_debuff"] = appr_sp3

    return mods, appears
