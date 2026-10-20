#!/usr/bin/env python3
"""
Bot Ability Implementation: 野牛 (Tantrum)
=========================================
Bot ID: tantrum_gs_kabam
阵营: 霸天虎 (Decepticon) | 职业: 格斗系 (Brawler)

【官方技能真理源对照 (来自 Upstash KV 聚合 Priorities 清单)】：
-----------------------------------------------------------------------------
1. [被动 - 不可阻挡] (ID: 3438, pua_icon: 0xe915)
   - 进入防御状态 1.5 秒后，获得 4.5 秒不可阻挡增益 (灰色倒计时 1.5s 后变黄色不可阻挡)。
2. [被动 - 近战增益] (ID: 3450, pua_icon: 0xe412)
   - 前冲时 100% 获得一层近战增益，增加 24% 近战伤害，最大叠加 10 层 (无倒计时)。
     如果野牛后闪且身上没有不可阻挡状态，则失去所有近战增益。
3. [被动 - 天然护甲] (ID: 3451, pua_icon: 无)
   - +10% 永久护甲增益，无图标，不可被破甲移除。
4. [SP3 - 不可阻挡] (ID: 3453, pua_icon: 0xe915)
   - 技能结束后获得 7.5 秒不可阻挡增益。
5. [SP3 - 近战增益] (ID: 3454, pua_icon: 0xe412)
   - 技能结束后获得 3 层近战增益，每层增加 24% 近战伤害，最大叠加 10 层。
-----------------------------------------------------------------------------
"""

from ..core import (
    make_attack_boost_statmod,
    make_armor_up_statmod,
    make_unstoppable_statmod,
    validate_color_code,
    validate_statmod,
    validate_appear,
)
from ..registry import register_bot

BOT_ID = "tantrum_gs_kabam"


@register_bot(BOT_ID, name_zh="野牛", desc="格斗系狂暴冲锋者，防御蓄力爆发霸体，前冲叠加巨额近战伤害，天然重甲")
def build_tantrum_abilities(base_hp: float = 36000.0, base_atk: float = 2150.0):
    mods = {}
    appears = {}

    # 1a. 防御蓄力 (ID: 3438a): 防御进入时触发灰色倒计时图标 1.5 秒 (参考 Prowl 充能灰色图标机制)
    appr_charge = {
        "id": "appr_tantrum_block_charge",
        "a": "",
        "s": "",
        "l": "坚守防御1.5秒获得不可阻挡",
        "ss": "坚守防御1.5秒获得不可阻挡",
        "t": "\uE915",  # 不可阻挡图标
        "f": "",
        "st": "",
        "ps": "不可阻挡充能",
        "pl": "蓄力中",
        "tc": "CBD5E1",  # 银灰/灰色
        "gt": "CBD5E1",
        "gb": "94A3B8",  # 板岩灰
    }
    validate_appear(appr_charge)
    appears["appr_tantrum_block_charge"] = appr_charge

    mod_charge = {
        "id": "tantrum_block_charge",
        "t": "attack_buff",
        "tm": "",
        "tr": ["manual"],
        "uit": [],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.0,
        "d": 1.5,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "tantrum_charge",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_tantrum_block_charge"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_charge)
    mods["tantrum_block_charge"] = mod_charge

    # 1b. 防御不可阻挡 (ID: 3438b): 防御持续 1.5s 后由 NativeHook 主动施加 4.5s 霸体
    m_unstop, a_unstop = make_unstoppable_statmod(
        mod_id="tantrum_block_unstoppable",
        duration=4.5,
        trigger="manual",
        trigger_scope="",
        appr_id="appr_tantrum_block_unstoppable",
        callout_text="不可阻挡",
        show_callout=True,
        pua_icon="\uE915",
        color_hex="FFAA00",
    )
    mods.update(m_unstop)
    appears.update(a_unstop)

    # 2. 前冲近战增益 (ID: 3450): 前冲 100% 获得 24% 近战增益 (最多 10 层，后闪且无霸体清除)
    m_dash, a_dash = make_attack_boost_statmod(
        mod_id="tantrum_dash_melee_buff",
        duration=0.0,
        attack_bonus=0.24,
        chance=1.0,
        trigger="onPlayerStateEnter",
        trigger_scope="state=Dash",
        appr_id="appr_tantrum_dash_melee_buff",
        callout_text="近战增益",
        show_callout=True,
        pua_icon="\uE412",
        stackable=True,
        max_stacks=10,
    )
    mods.update(m_dash)
    appears.update(a_dash)

    # 3. 天然护甲 (ID: 3451): +10% 永久护甲，不可破甲移除
    m_arm, a_arm = make_armor_up_statmod(
        mod_id="tantrum_innate_armor",
        duration=0.0,
        armor_bonus=0.10,
        chance=1.0,
        trigger="always",
        trigger_scope="",
        appr_id="appr_tantrum_innate_armor",
        callout_text="护甲",
        show_callout=False,
        stackable=False,
    )
    mods.update(m_arm)
    appears.update(a_arm)

    # 4. SP3 不可阻挡 (ID: 3453): 技能结束获得 7.5s 不可阻挡
    m_sp3_u, a_sp3_u = make_unstoppable_statmod(
        mod_id="tantrum_sp3_unstoppable",
        duration=7.5,
        trigger="onSpecial3Expiry",
        trigger_scope="",
        appr_id="appr_tantrum_sp3_unstoppable",
        callout_text="不可阻挡",
        show_callout=True,
        pua_icon="\uE915",
    )
    mods.update(m_sp3_u)
    appears.update(a_sp3_u)

    # 5. SP3 近战增益 (ID: 3454): 技能结束获得 3 层近战增益 (+72% 伤害)
    m_sp3_atk, a_sp3_atk = make_attack_boost_statmod(
        mod_id="tantrum_sp3_melee_buff",
        duration=0.0,
        attack_bonus=0.72,
        chance=1.0,
        trigger="onSpecial3Expiry",
        trigger_scope="",
        appr_id="appr_tantrum_sp3_melee_buff",
        callout_text="近战增益",
        show_callout=True,
        pua_icon="\uE412",
        stackable=True,
        max_stacks=10,
    )
    mods.update(m_sp3_atk)
    appears.update(a_sp3_atk)

    return mods, appears
