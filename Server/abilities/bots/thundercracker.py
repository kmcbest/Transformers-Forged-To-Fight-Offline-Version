#!/usr/bin/env python3
"""
Bot Ability Implementation: 惊天雷 (Thundercracker)
===================================================
Bot ID: thundercracker_gs_leader2015
阵营: 霸天虎 (Decepticon) | 职业: 爆破系 (Demolition)

【官方技能真理源对照 (来自 Upstash KV 聚合 Priorities 清单)】：
-----------------------------------------------------------------------------
1. [被动 - 近战0暴] (ID: 3404, pua_icon: 无)
   - 惊天雷所有攻击不产生暴击，如果随机数出现暴击，则强制以白字显示伤害，而不是黄字。
2. [被动 - 净化] (ID: 3409, pua_icon: 无)
   - 重击开始时，净化身上所有流血，燃烧，震击，酸液，逆火和目眩减益。
3. [被动 - 燃烧] (ID: 3410, pua_icon: 0xe41d)
   - 每净化一个减益，就给对方施加一层燃烧，造成攻击力80%的伤害，持续7秒。
4. [SP1 - 近战增益] (ID: 3420, pua_icon: 0xe412)
   - 除第一击外，所有攻击获得10%的近战增益，持续2秒。
5. [SP3 - 震击] (ID: 3422, pua_icon: 0xe914)
   - 当你的敌人认为你已陷入绝境时……粉碎他们。造成高额震击伤害。
-----------------------------------------------------------------------------
"""

from ..core import (
    make_attack_boost_statmod,
    make_burn_statmod,
    make_shock_statmod,
    validate_color_code,
    validate_statmod,
)
from ..registry import register_bot

BOT_ID = "thundercracker_gs_leader2015"


@register_bot(BOT_ID, name_zh="惊天雷", desc="爆破系重型战机，全攻击纯白字零暴击，重击强力净化全减益并反噬高额燃烧")
def build_thundercracker_abilities(base_hp: float = 29000.0, base_atk: float = 2500.0):
    mods = {}
    appears = {}

    # 1. 被动近战0暴 (ID: 3404): 强制白字伤害
    validate_color_code("3B82F6", "tc_zero_crit_tc")
    validate_color_code("1D4ED8", "tc_zero_crit_gb")
    appr_zero = {
        "id": "appr_thundercracker_zero_crit",
        "a": "精准打击",
        "s": "近战0暴",
        "l": "所有攻击不产生暴击，全部以纯白字绝对伤害结算",
        "ss": "全攻击锁定白字",
        "t": "\uE406",
        "f": "",
        "st": "绝对打击",
        "ps": "精准打击",
        "pl": "精准打击生效中",
        "tc": "3B82F6",
        "gt": "3B82F6",
        "gb": "1D4ED8",
    }
    mod_zero = {
        "id": "thundercracker_zero_crit",
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
        "g": "zero_crit",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_thundercracker_zero_crit"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_zero)
    mods["thundercracker_zero_crit"] = mod_zero
    appears["appr_thundercracker_zero_crit"] = appr_zero

    # 2. 被动重击净化 (ID: 3409): 重击开始净化所有DOT减益
    appr_purify = {
        "id": "appr_thundercracker_heavy_purify",
        "a": "过载净化",
        "s": "过载净化",
        "l": "重击发起时净化所有流血/燃烧/震击等减益",
        "ss": "重击全减益净化",
        "t": "\uE950",
        "f": "",
        "st": "净化",
        "ps": "过载净化",
        "pl": "过载净化生效中",
        "tc": "10B981",
        "gt": "10B981",
        "gb": "059669",
    }
    mod_purify = {
        "id": "thundercracker_heavy_purify",
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
        "g": "purify",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_thundercracker_heavy_purify"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_purify)
    mods["thundercracker_heavy_purify"] = mod_purify
    appears["appr_thundercracker_heavy_purify"] = appr_purify

    # 3. 被动净化转燃烧 (ID: 3410): 净化减益对目标施加 7 秒 80% ATK 燃烧
    m_burn, a_burn = make_burn_statmod(
        mod_id="thundercracker_purify_burn",
        duration=7.0,
        total_dmg=float(round(base_atk * 0.80)),
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Heavy",
        appr_id="appr_thundercracker_purify_burn",
        callout_text="燃烧",
        show_callout=True,
        pua_icon="\uE41D",
    )
    mods.update(m_burn)
    appears.update(a_burn)

    # 4. SP1 近战增益 (ID: 3420): 除第一击外获得 10% 近战增益 2s
    m_sp1, a_sp1 = make_attack_boost_statmod(
        mod_id="thundercracker_sp1_melee_buff",
        duration=2.0,
        attack_bonus=0.10,
        chance=1.0,
        trigger="onSpecial1Activate",
        appr_id="appr_thundercracker_sp1_melee_buff",
        callout_text="近战增益",
        show_callout=True,
        pua_icon="\uE412",
    )
    mods.update(m_sp1)
    appears.update(a_sp1)

    # 5. SP3 震击 (ID: 3422): 绝境震击 (造成 150% ATK 震击 10s)
    m_sp3, a_sp3 = make_shock_statmod(
        mod_id="thundercracker_sp3_shock",
        duration=10.0,
        total_dmg=float(round(base_atk * 1.50)),
        chance=1.0,
        trigger="onSpecial3Activate",
        appr_id="appr_thundercracker_sp3_shock",
        callout_text="震击",
        show_callout=True,
        pua_icon="\uE914",
    )
    mods.update(m_sp3)
    appears.update(a_sp3)

    return mods, appears
