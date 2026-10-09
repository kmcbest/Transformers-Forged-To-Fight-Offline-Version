#!/usr/bin/env python3
"""
Bot Ability Implementation: 喷气机 (Ramjet)
===========================================
Bot ID: ramjet_gs_deluxe2008
阵营: 霸天虎 (Decepticon) | 职业: 破坏系 (Demolition)

【官方技能真理源对照 (来自 Upstash KV 聚合 Priorities 清单)】：
-----------------------------------------------------------------------------
1. [被动 - 燃烧眩晕 / Burn Stun] (ID: 3237, pua_icon: 0xe605, category: passive)
   - 官方描述: "重击命中处于燃烧状态的对手，100%概率触发眩晕，持续3秒"
   - 实现方案:
     ramjet_heavy_burn_stun: 触发 onHit, level=Heavy;opp.status=dmg_burn, 100% 概率击晕对手 3.0 秒。

2. [被动 - 重击霸体 / Unstoppable Heavy] (ID: 3251, pua_icon: 0xe915, category: passive)
   - 官方描述: "重击全程进入不可阻挡状态"
   - 实现方案:
     ramjet_heavy_unstoppable: 触发 onPlayerStateEnter, state=HeavyCharge,HeavyAttack, 获得 1.8 秒霸体 (不可阻挡)。

3. [SP1 - 燃烧 / Missile Burn] (ID: 3252, pua_icon: 0xe41d, category: sp1)
   - 官方描述: "每一击有60%的概率施加随机1~4层燃烧，每一层施加攻击力35%的伤害，持续6秒。 //用例：因为SP1是两击，所以最多可以施加8层燃烧"
   - 实现方案:
     ramjet_s1_burn: 触发 onHit, level=Special1, 60% 概率施加 6.0 秒燃烧 (35% ATK 伤害, 可堆叠)。

4. [SP2 - 燃烧 / Cluster Bomb Burn] (ID: 3253, pua_icon: 0xe41d, category: sp2)
   - 官方描述: "每一击有100%的概率施加燃烧，造成攻击力70%的伤害，持续6秒。"
   - 实现方案:
     ramjet_s2_burn: 触发 onHit, level=Special2, 100% 概率施加 6.0 秒燃烧 (70% ATK 伤害)。

5. [SP3 - 互晕 / Crash Headbutt Self & Opponent Stun] (ID: 3254, pua_icon: 0xe605, category: sp3)
   - 官方描述: "技能完成后，100%概率给对手和自己同时施加眩晕，对手眩晕4秒，自己眩晕1秒。"
   - 实现方案:
     ramjet_s3_stun_opp: 触发 onSpecial3Expiry, 100% 概率对对手施加 4.0 秒眩晕。
     ramjet_s3_stun_self: 触发 onSpecial3Expiry, 100% 概率对自己施加 1.0 秒眩晕。
-----------------------------------------------------------------------------
"""

from ..core import make_stun_statmod, make_unstoppable_statmod, make_burn_statmod
from ..registry import register_bot

BOT_ID = "ramjet_gs_deluxe2008"


@register_bot(BOT_ID, name_zh="喷气机", desc="破坏系自杀撞击者，重击霸体与晕火、SP1/SP2连环轰炸、SP3自爆撞击互晕")
def build_ramjet_abilities(base_hp: float = 33025.0, base_atk: float = 2237.0):
    mods = {}
    appears = {}
    buffs = {}

    # 1. 重击命中燃烧对手 100% 眩晕 3 秒
    m1, a1 = make_stun_statmod(
        mod_id="ramjet_heavy_burn_stun",
        duration=3.0,
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Heavy;opp.status=dmg_burn",
        callout_text="眩晕",
        pua_icon="\uE605",
    )
    mods.update(m1)
    appears.update(a1)

    # 2. 重击全程不可阻挡 (霸体)
    m2, a2 = make_unstoppable_statmod(
        mod_id="ramjet_heavy_unstoppable",
        duration=1.8,
        trigger="onPlayerStateEnter",
        trigger_scope="state=HeavyCharge,HeavyAttack",
        callout_text="不可阻挡",
        pua_icon="\uE915",
    )
    mods.update(m2)
    appears.update(a2)

    # 3. SP1 燃烧 (35% ATK: 2237 * 0.35 = 783, 持续 6 秒, 60% 几率, 随机 1~4 层)
    m3, a3 = make_burn_statmod(
        mod_id="ramjet_s1_burn",
        duration=6.0,
        total_dmg=float(round(base_atk * 0.35)),
        chance=0.60,
        trigger="onHit",
        trigger_scope="level=Special1",
        callout_text="燃烧",
        stackable=True,
        pua_icon="\uE41D",
    )
    mods.update(m3)
    appears.update(a3)

    for i in range(2, 5):
        m_s, a_s = make_burn_statmod(
            mod_id=f"ramjet_s1_burn_stack_{i}",
            duration=6.0,
            total_dmg=float(round(base_atk * 0.35)),
            chance=1.0,
            trigger="onHit",
            trigger_scope="level=Special1",
            callout_text="燃烧",
            stackable=True,
            pua_icon="\uE41D",
        )
        mods.update(m_s)
        appears.update(a_s)

    # 4. SP2 燃烧 (70% ATK: 2237 * 0.7 = 1566, 持续 6 秒, 100% 几率)
    m4, a4 = make_burn_statmod(
        mod_id="ramjet_s2_burn",
        duration=6.0,
        total_dmg=float(round(base_atk * 0.70)),
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Special2",
        callout_text="燃烧",
        stackable=True,
        pua_icon="\uE41D",
    )
    mods.update(m4)
    appears.update(a4)

    # 5.1 SP3 对方眩晕 4 秒
    m5_opp, a5_opp = make_stun_statmod(
        mod_id="ramjet_s3_stun_opp",
        duration=4.0,
        chance=1.0,
        trigger="onSpecial3Expiry",
        target_actor="opponent",
        appr_id="appr_ramjet_s3_stun_opp",
        callout_text="眩晕",
        pua_icon="\uE605",
    )
    mods.update(m5_opp)
    appears.update(a5_opp)

    # 5.2 SP3 自己眩晕 1 秒
    m5_self, a5_self = make_stun_statmod(
        mod_id="ramjet_s3_stun_self",
        duration=1.0,
        chance=1.0,
        trigger="onSpecial3Expiry",
        target_actor="self",
        appr_id="appr_ramjet_s3_stun_self",
        callout_text="眩晕",
        pua_icon="\uE605",
    )
    mods.update(m5_self)
    appears.update(a5_self)

    return mods, appears, buffs
