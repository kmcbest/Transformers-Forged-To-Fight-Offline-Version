#!/usr/bin/env python3
"""
Bot Ability Implementation: 碎骨魔 (Bonecrusher ROTF)
===================================================
Bot ID: bonecrusher_cin_rotf
阵营: 霸天虎 (Decepticon) | 职业: 格斗系 (Warrior)

【官方技能真理源对照 (来自 Upstash KV 聚合 72 Priorities 清单)】：
-----------------------------------------------------------------------------
1. [SP1 - 流血 / Bleed] (ID: 2969, category: sp1)
   - 官方描述: "每一击90%的概率触发流血，造成攻击力115%的伤害，持续2秒。"
2. [SP2 - 流血 / Bleed] (ID: 2970, category: sp2)
   - 官方描述: "每一击71%的概率触发流血，造成攻击力72%的伤害，持续7秒。"
3. [SP3 - 流血 / Bleed] (ID: 2971, category: sp3)
   - 官方描述: "每一击45%的概率触发流血，造成攻击力198%的伤害，持续18秒。"
-----------------------------------------------------------------------------
"""

from ..core import make_bleed_statmod
from ..registry import register_bot

BOT_ID = "bonecrusher_cin_rotf"


@register_bot(BOT_ID, name_zh="碎骨魔", desc="格斗系，多段特技高概率流血")
def build_bonecrusher_abilities(base_hp: float = 31468.0, base_atk: float = 2398.0):
    mods = {}
    appears = {}
    buffs = {}

    # 1. ID 2969: SP1 每一击 90% 概率流血 (115% ATK, 2.0s)
    sp1_bleed_dmg = float(round(base_atk * 1.15, 2))
    m1, a1 = make_bleed_statmod(
        mod_id="bonecrusher_sp1_bleed",
        duration=2.0,
        total_dmg=sp1_bleed_dmg,
        chance=0.90,
        trigger="onHit",
        trigger_scope="level=Special1",
        appr_id="appr_bonecrusher_bleed",
        callout_text="流血",
        stackable=True,
    )
    mods.update(m1)
    appears.update(a1)

    # 2. ID 2970: SP2 每一击 71% 概率流血 (72% ATK, 7.0s)
    sp2_bleed_dmg = float(round(base_atk * 0.72, 2))
    m2, a2 = make_bleed_statmod(
        mod_id="bonecrusher_sp2_bleed",
        duration=7.0,
        total_dmg=sp2_bleed_dmg,
        chance=0.71,
        trigger="onHit",
        trigger_scope="level=Special2",
        appr_id="appr_bonecrusher_bleed",
        callout_text="流血",
        stackable=True,
    )
    mods.update(m2)
    appears.update(a2)

    # 3. ID 2971: SP3 每一击 45% 概率流血 (198% ATK, 18.0s)
    sp3_bleed_dmg = float(round(base_atk * 1.98, 2))
    m3, a3 = make_bleed_statmod(
        mod_id="bonecrusher_sp3_bleed",
        duration=18.0,
        total_dmg=sp3_bleed_dmg,
        chance=0.45,
        trigger="onHit",
        trigger_scope="level=Special3",
        appr_id="appr_bonecrusher_bleed",
        callout_text="流血",
        stackable=True,
    )
    mods.update(m3)
    appears.update(a3)

# 4. [既有技能保留] 受到近战暴击流血 7 秒 DOT (89.6% ATK, 90% 几率, 作用于 opponent, 可叠加)
    struck_bleed_dmg = float(round(base_atk * 0.896, 2))
    m4, a4 = make_bleed_statmod(
        mod_id="bonecrusher_struck_crit_bleed",
        duration=7.0,
        total_dmg=struck_bleed_dmg,
        chance=0.90,
        trigger="onStruckCrit",
        trigger_scope="level=Melee",
        appr_id="appr_bonecrusher_bleed",
        callout_text="流血",
        stackable=True,
        buff_id="dmg_bleed",
        target_actor="opponent",
    )
    mods.update(m4)
    appears.update(a4)

    # 5. [既有技能保留] 重击命中流血 5.6 秒 DOT (45% ATK, 70% 几率)
    heavy_bleed_dmg = float(round(base_atk * 0.45, 2))
    m5, a5 = make_bleed_statmod(
        mod_id="bonecrusher_heavy_bleed",
        duration=5.6,
        total_dmg=heavy_bleed_dmg,
        chance=0.70,
        trigger="onHit",
        trigger_scope="level=Heavy",
        appr_id="appr_bonecrusher_bleed",
        callout_text="流血",
    )
    mods.update(m5)
    appears.update(a5)

    return mods, appears, buffs

