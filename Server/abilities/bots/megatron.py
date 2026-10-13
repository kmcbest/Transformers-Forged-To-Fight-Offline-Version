#!/usr/bin/env python3
"""
Bot Ability Implementation: 领袖威震天 (Megatron Leader)
======================================================
Bot ID: megatron_gs_leader2015
阵营: 霸天虎 (Decepticon) | 职业: 战术系 (Tactician)

【官方技能真理源对照 (来自 Upstash KV 聚合 Priorities 清单)】：
-----------------------------------------------------------------------------
1. [被动 - 融合炮] (ID: 3121, pua_icon: 0xe910)
   - 融合炮：每6秒充满一层融合炮，最多三层。有融合炮增益时，重击飞行速度+50%。
2. [SP2 - 攻击减益] (ID: 3129, pua_icon: 0xe916)
   - 100%的概率施加44%的攻击减益，持续10秒。
3. [SP3 - 震击] (ID: 3130, pua_icon: 0xe914)
   - 100%的概率施加震击，造成攻击300%的伤害，持续20秒。融合炮过载：本局可无限使用，不消耗。
4. [SP1 - 破甲] (ID: 3137, pua_icon: 0xe516)
   - 100%的概率施加38%的破甲，持续10秒。
5. [被动 - 减益融合] (ID: 3138, pua_icon: 0xe60f)
   - 如果重击击中对方时对方身上有带倒计时的减益，则该减益变为不带倒计时的永久状态。
-----------------------------------------------------------------------------
"""

from ..core import (
    make_armor_break_statmod,
    make_shock_statmod,
    validate_color_code,
    validate_statmod,
)
from ..registry import register_bot

BOT_ID = "megatron_gs_leader2015"


@register_bot(BOT_ID, name_zh="威震天", desc="霸天虎最高领袖，融合炮自动充能蓄势，重击减益永久化，SP1高额破甲与SP3毁灭震击")
def build_megatron_abilities(base_hp: float = 31000.0, base_atk: float = 2450.0):
    mods = {}
    appears = {}

    # 1. 融合炮充能 (ID: 3121): 每 6s 充能 1 层，最多 3 层
    validate_color_code("8B5CF6", "fusion_cannon_tc")
    validate_color_code("6D28D9", "fusion_cannon_gb")
    appr_fusion = {
        "id": "appr_megatron_fusion_cannon",
        "a": "融合炮",
        "s": "融合炮",
        "l": "每6秒充能一层融合炮(上限3层)，重击飞行速度+50%",
        "ss": "融合炮充能",
        "t": "\uE910",
        "f": "",
        "st": "融合炮",
        "ps": "融合炮",
        "pl": "融合炮充能中",
        "tc": "8B5CF6",
        "gt": "8B5CF6",
        "gb": "6D28D9",
    }
    mod_fusion = {
        "id": "megatron_fusion_cannon",
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
        "st": 3,
        "g": "fusion_cannon",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_megatron_fusion_cannon"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_fusion)
    mods["megatron_fusion_cannon"] = mod_fusion
    appears["appr_megatron_fusion_cannon"] = appr_fusion

    # 2. SP2 攻击减益 (ID: 3129): 100% 施加 44% 攻击减益 10 秒
    appr_sp2_atk = {
        "id": "appr_megatron_sp2_atk_debuff",
        "a": "虚弱",
        "s": "虚弱",
        "l": "降低对手44%的攻击力",
        "ss": "攻击力削弱",
        "t": "\uE916",
        "f": "",
        "st": "攻击减益",
        "ps": "攻击减益",
        "pl": "攻击减益生效中",
        "tc": "EF4444",
        "gt": "EF4444",
        "gb": "B91C1C",
    }
    mod_sp2_atk = {
        "id": "megatron_sp2_atk_debuff",
        "t": "attack_debuff",
        "tm": "",
        "tr": ["onSpecial2Activate"],
        "uit": ["onSpecial2Activate"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.44,
        "d": 10.0,
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
        "a": ["appr_megatron_sp2_atk_debuff"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_sp2_atk)
    mods["megatron_sp2_atk_debuff"] = mod_sp2_atk
    appears["appr_megatron_sp2_atk_debuff"] = appr_sp2_atk

    # 3. SP3 震击与过载 (ID: 3130): 100% 施加 300% 震击 20s
    m_sp3_s, a_sp3_s = make_shock_statmod(
        mod_id="megatron_sp3_shock",
        duration=20.0,
        total_dmg=float(round(base_atk * 3.00)),
        chance=1.0,
        trigger="onSpecial3Activate",
        appr_id="appr_megatron_sp3_shock",
        callout_text="震击",
        show_callout=True,
        pua_icon="\uE914",
    )
    mods.update(m_sp3_s)
    appears.update(a_sp3_s)

    # 4. SP1 破甲 (ID: 3137): 100% 施加 38% 破甲 10 秒
    m_sp1_ab, a_sp1_ab = make_armor_break_statmod(
        mod_id="megatron_sp1_armor_break",
        duration=10.0,
        break_amount=0.38,
        chance=1.0,
        trigger="onSpecial1Activate",
        appr_id="appr_megatron_sp1_armor_break",
        callout_text="破甲",
        show_callout=True,
        pua_icon="\uE516",
    )
    mods.update(m_sp1_ab)
    appears.update(a_sp1_ab)

    # 5. 被动减益融合 (ID: 3138): 重击命中将对方带倒计时的减益化为永久
    appr_fusion_deb = {
        "id": "appr_megatron_debuff_fusion",
        "a": "减益融合",
        "s": "减益融合",
        "l": "重击命中将目标身上的限时减益永久化锁定",
        "ss": "减益永久锁定",
        "t": "\uE60F",
        "f": "",
        "st": "减益融合",
        "ps": "减益融合",
        "pl": "减益融合生效中",
        "tc": "A855F7",
        "gt": "A855F7",
        "gb": "7E22CE",
    }
    mod_fusion_deb = {
        "id": "megatron_debuff_fusion",
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
        "g": "debuff_fusion",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_megatron_debuff_fusion"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_fusion_deb)
    mods["megatron_debuff_fusion"] = mod_fusion_deb
    appears["appr_megatron_debuff_fusion"] = appr_fusion_deb

    return mods, appears
