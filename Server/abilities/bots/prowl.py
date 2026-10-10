#!/usr/bin/env python3
"""
Bot Ability Implementation: 警车 (Prowl)
=======================================
Bot ID: prowl_gs_deluxe2016
阵营: 汽车人 (Autobot) | 职业: 侦查系 (Scout)

【官方技能真理源对照 (来自在线优先实现)】：
-----------------------------------------------------------------------------
1. [SP1 - 能量燃烧 / Short Circuit Power Burn] (ID: 2735, pua_icon: 0xe607, category: sp1)
   - 官方描述: "100%概率触发能量燃烧，0.5秒内扣减对方最大能量（按三格满计）的40.5% //仅第一击触发"
   - 实现方案:
     prowl_s1_power_burn: 触发 onSpecial1Hit, index=0 (仅第一击), 100% 概率在 0.5 秒内抽取对方 1.215 格能量 (364.5 Mana)。

2. [SP2 - 远程伤害 / Ranged Damage Boost] (ID: 2736, pua_icon: 0xe41b, category: sp2)
   - 官方描述: "远程伤害提升50%，远程射速提升50%，持续6秒"
   - 实现方案:
     prowl_s2_ranged_boost: 触发 onSpecial2Activate, 持续 6.0 秒自身获得远程增益 (+50% 远程伤害, +50% 射速提升)。

3. [SP3 - 能量锁定 / Power Lock] (ID: 2737, pua_icon: 0xe523, category: sp3)
   - 官方描述: "技能发动时100%概率触发能量锁定，阻止对方获得能量，持续16秒"
   - 实现方案:
     prowl_s3_power_lock: 触发 onSpecial3Activate, 100% 概率对对手施加 16.0 秒能量锁定，彻底压制并阻止对手获得能量。
-----------------------------------------------------------------------------
"""

from ..core import make_power_leak_statmod, make_ranged_boost_statmod, make_power_lock_statmod
from ..registry import register_bot

BOT_ID = "prowl_gs_deluxe2016"


@register_bot(BOT_ID, name_zh="警车", desc="侦查系神射副官，SP1第一击强力烧能、SP2高速加伤连射、SP3长效锁定对手能量")
def build_prowl_abilities(base_hp: float = 30533.0, base_atk: float = 2329.0):
    """
    根据基准属性生成警车全部专属能力修饰器。
    基准 5星50级: HP = 30533.0, ATK = 2329.0
    """
    mods = {}
    appears = {}
    buffs = {}

    # 1. SP1 能量燃烧: 第一击命中对手时触发，0.5 秒内抽取三格满气的 40.5% (1.215 格 = 364.5 Mana)
    m1, a1 = make_power_leak_statmod(
        mod_id="prowl_s1_power_burn",
        duration=0.5,
        drain_bars=1.215,  # 三格总能量扣除 40.5% (0.405 * 3 = 1.215 格 = 364.5 Mana)
        chance=1.0,
        trigger="onSpecial1Hit",
        trigger_scope="index=0",  # 仅第一击触发
        appr_id="appr_prowl_s1_power_burn",
        callout_text="能量燃烧",
        pua_icon="\uE607",
        color_hex="FF0000",
        gradient_bottom="FF0000",
    )
    mods.update(m1)
    appears.update(a1)

    # 2. SP2 远程伤害: 激活 SP2 时触发，持续 6 秒提升 50% 远程伤害与 50% 射速
    m2, a2 = make_ranged_boost_statmod(
        mod_id="prowl_s2_ranged_boost",
        duration=6.0,
        damage_bonus=0.50,
        speed_bonus=0.50,
        trigger="onSpecial2Activate",
        appr_id="appr_prowl_s2_ranged_boost",
        callout_text="远程增益",
        show_callout=True,
        pua_icon="\uE41B",
        color_hex="FFAA00",
        gradient_bottom="FF6600",
    )
    mods.update(m2)
    appears.update(a2)

    # 3. SP3 能量锁定: 激活 SP3 时 100% 概率触发，持续 16 秒阻止对方获得能量
    m3, a3 = make_power_lock_statmod(
        mod_id="prowl_s3_power_lock",
        duration=16.0,
        chance=1.0,
        trigger="onSpecial3Activate",
        appr_id="appr_prowl_s3_power_lock",
        callout_text="能量锁定",
        pua_icon="\uE523",
        color_hex="FF0000",
        gradient_bottom="FF0000",
    )
    mods.update(m3)
    appears.update(a3)

    return mods, appears, buffs
