#!/usr/bin/env python3
"""
Bot Ability Implementation: 飞标 (Swoop)
=======================================
Bot ID: swoop_gs_deluxe2008
阵营: 汽车人 (Autobot) | 职业: 科技系 (Tech)
模具母体: 喷气机 (Ramjet) | 特异性招式: 钢锁霸王龙重击火球喷吐
"""

from ..core import make_stun_statmod, make_burn_statmod
from ..registry import register_bot

BOT_ID = "swoop_gs_deluxe2008"


@register_bot(BOT_ID, name_zh="飞标", desc="汽车人机器恐龙空中先锋，重击兽嘴烈火吐息、双翼轰炸燃烧、科技系属性克制")
def build_swoop_abilities(base_hp: float = 39200.0, base_atk: float = 2980.0):
    mods = {}
    appears = {}
    buffs = {}

    # 1. 重击火球喷吐：命中目标 100% 几率施加 4 秒燃烧 (40% ATK 伤害)
    m_heavy, a_heavy = make_burn_statmod(
        mod_id="swoop_heavy_fireball_burn",
        duration=4.0,
        total_dmg=float(round(base_atk * 0.40)),
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Heavy",
        callout_text="烈焰吐息",
        stackable=True,
        pua_icon="\uE41D",
    )
    mods.update(m_heavy)
    appears.update(a_heavy)

    # 2. SP1 空对地导弹轰炸：60% 几率施加 6 秒燃烧
    m1, a1 = make_burn_statmod(
        mod_id="swoop_s1_burn",
        duration=6.0,
        total_dmg=float(round(base_atk * 0.35)),
        chance=0.60,
        trigger="onHit",
        trigger_scope="level=Special1",
        callout_text="燃烧",
        stackable=True,
        pua_icon="\uE41D",
    )
    mods.update(m1)
    appears.update(a1)

    # 3. SP2 翼刃俯冲：100% 施加 6 秒破甲与眩晕
    m2_stun, a2_stun = make_stun_statmod(
        mod_id="swoop_s2_stun",
        duration=3.5,
        chance=0.80,
        trigger="onHit",
        trigger_scope="level=Special2",
        callout_text="眩晕",
        pua_icon="\uE605",
    )
    mods.update(m2_stun)
    appears.update(a2_stun)

    # 4. SP3 终极翼龙火风暴：100% 施加强力燃烧 (100% ATK 伤害)
    m3, a3 = make_burn_statmod(
        mod_id="swoop_s3_incinerate",
        duration=6.0,
        total_dmg=float(round(base_atk * 1.00)),
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Special3",
        callout_text="焚尽",
        stackable=True,
        pua_icon="\uE41D",
    )
    mods.update(m3)
    appears.update(a3)

    return mods, appears, buffs
