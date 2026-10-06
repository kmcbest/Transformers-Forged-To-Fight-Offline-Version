#!/usr/bin/env python3
"""
Bot Ability Implementation: 千斤顶 (Wheeljack)
=============================================
Bot ID: wheeljack_gs_mp20
阵营: 汽车人 (Autobot) | 职业: 科技系 (Tech)

【官方技能真理源对照 (来自在线优先实现)】：
-----------------------------------------------------------------------------
千斤顶的 SP1、SP2、SP3 均配置了三项核心机制：
1. [震击 / Shock] (pua_icon: 0xe914)
   - 描述: "60%概率施加震击，造成攻击力200%的伤害，持续6秒"
   - 实现方案: make_shock_statmod(trigger=onSpecialActivate, chance=0.60, total_dmg=2.0*ATK, duration=6.0)

2. [能量流失 / Power Leak] (pua_icon: 0xe607)
   - 描述: "30%的概率造成能量流失，在3秒内扣除对方一格能量的40%。"
   - 实现方案: make_power_leak_statmod(trigger=onSpecialActivate, chance=0.30, drain_bars=0.40, duration=3.0)

3. [眩晕 / Stun] (pua_icon: 0xe605)
   - 描述: "10%的概率造成眩晕，持续3秒"
   - 实现方案: make_stun_statmod(trigger=onSpecialActivate, chance=0.10, duration=3.0)
-----------------------------------------------------------------------------
"""

from ..core import make_shock_statmod, make_power_leak_statmod, make_stun_statmod
from ..registry import register_bot

BOT_ID = "wheeljack_gs_mp20"


@register_bot(BOT_ID, name_zh="千斤顶", desc="科技系发明家，特殊技附带震击、能量流失与击晕三重科技打击")
def build_wheeljack_abilities(base_hp: float = 32402.0, base_atk: float = 2306.0):
    """
    根据基准属性生成千斤顶全部专属能力修饰器。
    基准 5星50级 ATK = 2306.0
    """
    mods = {}
    appears = {}
    buffs = {}

    # 为 SP1, SP2, SP3 分别装配三合一机制 (命中对手时按概率施加)
    sp_levels = [
        ("sp1", "level=Special1", "Special 1", "原型"),
        ("sp2", "level=Special2", "Special 2", "迭代"),
        ("sp3", "level=Special3", "Special 3", "完美"),
    ]

    for sp_key, sp_scope, sp_label, sp_title in sp_levels:
        # 1. 震击 (Shock DOT): 60% 几率 200% ATK 持续 6 秒 (减益红)
        m_shock, a_shock = make_shock_statmod(
            mod_id=f"wheeljack_{sp_key}_shock",
            duration=6.0,
            total_dmg=float(round(base_atk * 2.0)),
            chance=0.60,
            trigger="onHit",
            trigger_scope=sp_scope,
            appr_id=f"appr_wheeljack_{sp_key}_shock",
            callout_text="震击",
            pua_icon="\uE914",
            color_hex="FF0000",
            gradient_bottom="FF0000",
        )
        mods.update(m_shock)
        appears.update(a_shock)

        # 2. 能量流失 (Power Leak): 30% 几率 3 秒内抽取 40% 一格能量 (减益红)
        m_leak, a_leak = make_power_leak_statmod(
            mod_id=f"wheeljack_{sp_key}_leak",
            duration=3.0,
            drain_bars=0.40,
            chance=0.30,
            trigger="onHit",
            trigger_scope=sp_scope,
            appr_id=f"appr_wheeljack_{sp_key}_leak",
            callout_text="能量流失",
            pua_icon="\uE607",
            color_hex="FF0000",
            gradient_bottom="FF0000",
        )
        mods.update(m_leak)
        appears.update(a_leak)

        # 3. 眩晕 (Stun): 10% 几率造成 3 秒眩晕
        m_stun, a_stun = make_stun_statmod(
            mod_id=f"wheeljack_{sp_key}_stun",
            duration=3.0,
            chance=0.10,
            trigger="onHit",
            trigger_scope=sp_scope,
            appr_id=f"appr_wheeljack_{sp_key}_stun",
            callout_text="眩晕",
            pua_icon="\uE605",
            color_hex="FFE000",
            gradient_bottom="FFAA00",
        )
        mods.update(m_stun)
        appears.update(a_stun)

    return mods, appears, buffs
