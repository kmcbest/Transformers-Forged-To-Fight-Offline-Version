#!/usr/bin/env python3
"""
Bot Ability Implementation: 横炮 (Sideswipe)
===========================================
Bot ID: sideswipe_gs
阵营: 汽车人 (Autobot) | 职业: 侦察兵 (Scout)

【官方技能真理源对照 (来自 Upstash KV 聚合 Priorities 清单)】：
-----------------------------------------------------------------------------
1. [SP1 - 暴击几率 / Crit Rate] (ID: 2836, pua_icon: 0xe40d, category: sp1)
   - 官方描述: "本技能内+25.5%暴击率 //倒计时在技能结束后消失"
   - 实现方案:
     sideswipe_s1_crit_rate: 触发 onSpecial1Activate, 100% 概率获得 2.5 秒暴击几率加成 (+25.5%)。

2. [SP1 - 眩晕 / Stun] (ID: 2825, pua_icon: 0xe605, category: sp1)
   - 官方描述: "//几拳就可以了，但用闪踢看起来更酷。 40%的概率击晕对手2.5秒"
   - 实现方案:
     sideswipe_s1_stun: 触发 onHit, level=Special1, 40% 概率击晕对手 2.5 秒。

3. [SP2 - 燃烧 / Burn] (ID: 2834, pua_icon: 0xe41d, category: sp2)
   - 官方描述: "最后一击100%几率造成燃烧，施加攻击力80%的伤害，持续6秒。"
   - 实现方案:
     sideswipe_s2_burn: 触发 onHit, level=Special2, 100% 概率施加 6.0 秒燃烧 (80% ATK 伤害)。

4. [SP3 - 燃烧 / Burn] (ID: 2835, pua_icon: 0xe41d, category: sp3)
   - 官方描述: "最后一击100%几率造成燃烧，施加攻击力100%的伤害，持续4秒。"
   - 实现方案:
     sideswipe_s3_burn: 触发 onHit, level=Special3, 100% 概率施加 4.0 秒燃烧 (100% ATK 伤害)。

5. [SP3 - 驱散 / Nullify] (ID: 2837, pua_icon: 0xe950, category: sp3)
   - 官方描述: "除最后一击外，每一击有60%的概率驱散对方一个增益"
   - 实现方案:
     sideswipe_s3_nullify: 触发 onHit, level=Special3, 60% 概率驱散对方 1 个增益。
-----------------------------------------------------------------------------
"""

from ..core import make_crit_rate_statmod, make_stun_statmod, make_burn_statmod, make_nullify_statmod
from ..registry import register_bot

BOT_ID = "sideswipe_gs"


@register_bot(BOT_ID, name_zh="横炮", desc="侦察兵迅捷突击手，SP1暴击闪踢眩晕、SP2/SP3排气管烈焰燃烧与增益驱散")
def build_sideswipe_abilities(base_hp: float = 26794.0, base_atk: float = 2698.0):
    mods = {}
    appears = {}
    buffs = {}

    # 1. SP1 暴击几率 (+25.5%, 持续 2.5 秒)
    m1, a1 = make_crit_rate_statmod(
        mod_id="sideswipe_s1_crit_rate",
        duration=2.5,
        crit_bonus=0.255,
        chance=1.0,
        trigger="onSpecial1Activate",
        callout_text="暴击几率",
        pua_icon="\uE40D",
    )
    mods.update(m1)
    appears.update(a1)

    # 2. SP1 眩晕 (40% 几率, 持续 2.5 秒)
    m2, a2 = make_stun_statmod(
        mod_id="sideswipe_s1_stun",
        duration=2.5,
        chance=0.40,
        trigger="onHit",
        trigger_scope="level=Special1",
        callout_text="眩晕",
        pua_icon="\uE605",
    )
    mods.update(m2)
    appears.update(a2)

    # 3. SP2 燃烧 (80% ATK: 2698 * 0.8 = 2158, 持续 6 秒, 100% 几率)
    m3, a3 = make_burn_statmod(
        mod_id="sideswipe_s2_burn",
        duration=6.0,
        total_dmg=float(round(base_atk * 0.80)),
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Special2",
        callout_text="燃烧",
        stackable=True,
        pua_icon="\uE41D",
    )
    mods.update(m3)
    appears.update(a3)

    # 4. SP3 燃烧 (100% ATK: 2698 * 1.0 = 2698, 持续 4 秒, 100% 几率)
    m4, a4 = make_burn_statmod(
        mod_id="sideswipe_s3_burn",
        duration=4.0,
        total_dmg=float(round(base_atk * 1.00)),
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Special3",
        callout_text="燃烧",
        stackable=True,
        pua_icon="\uE41D",
    )
    mods.update(m4)
    appears.update(a4)

    # 5. SP3 驱散 (60% 几率驱散一个正面增益)
    m5, a5 = make_nullify_statmod(
        mod_id="sideswipe_s3_nullify",
        target_categories=["melee", "ranged", "special"],
        max_stacks_per_cat=1,
        chance=0.60,
        trigger="onHit",
        trigger_scope="level=Special3",
        callout_text="驱散",
        pua_icon="\uE950",
    )
    mods.update(m5)
    appears.update(a5)

    return mods, appears, buffs
