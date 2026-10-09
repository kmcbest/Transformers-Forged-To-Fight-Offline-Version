#!/usr/bin/env python3
"""
Bot Ability Implementation: 恐龙勇士 (Dinobot BW)
=================================================
Bot ID: dinobot_bw_kabam
阵营: 巨无霸 (Maximal) | 职业: 战术系 (Tactician)

【官方技能真理源对照 (来自 Upstash KV 聚合 Priorities 清单)】：
-----------------------------------------------------------------------------
1. [被动 - 重击流血 / Heavy Crit Bleed] (ID: 2505, pua_icon: 0xe401, category: passive)
   - 官方描述: "重击命中并出暴击时：100%几率触发流血，造成攻击力80%的伤害，持续5秒。"
   - 实现方案:
     dinobot_heavy_crit_bleed:
       触发 onCrit, level=Heavy, 100% 概率施加 5.0 秒流血 debuff (80% base_atk 伤害),
       作用于 opponent, 红色血条圆环图标 (PUA: 0xe401, Hex: FF0000 / B91C1C),
       呼出文字: "BLEED"。
-----------------------------------------------------------------------------
"""

from ..core import make_bleed_statmod
from ..registry import register_bot

BOT_ID = "dinobot_bw_kabam"


@register_bot(BOT_ID, name_zh="恐龙勇士", desc="战术系刀客，重击暴击造成致命流血")
def build_dinobot_abilities(base_hp: float = 30844.0, base_atk: float = 2421.0):
    mods = {}
    appears = {}
    buffs = {}

    # 1. 重击暴击流血 (80% ATK: 2421 * 0.8 = 1937, 持续 5 秒, 100% 几率)
    m1, a1 = make_bleed_statmod(
        mod_id="dinobot_heavy_crit_bleed",
        duration=5.0,
        total_dmg=float(round(base_atk * 0.80)),
        chance=1.0,
        trigger="onCrit",
        trigger_scope="level=Heavy",
        appr_id="appr_dinobot_bleed",
        callout_text="BLEED",
        buff_id="dmg_bleed",
    )
    mods.update(m1)
    appears.update(a1)

    return mods, appears, buffs
