#!/usr/bin/env python3
"""
Bot Ability Implementation: 汽车大师 (Motormaster)
=================================================
Bot ID: motormaster_gs_voyager2015
阵营: 霸天虎 (Decepticon) | 职业: 格斗系 (Brawler)

【官方技能真理源对照 (来自 character_abilities / motormaster_gs_voyager2015.json)】：
-----------------------------------------------------------------------------
1. [被动 - 前冲 / Dashing]
   - 官方描述: "汽车大师以不可阻挡的力量向前冲锋，无视对手攻击的影响。"
   - 实现方案:
     a) motormaster_dash_unstoppable: 触发 onPlayerStateEnter, state=Dash, 持续 0.7 秒, 作用于 self,
        赋予 unstoppable 霸体 buff, 呼出 "UNSTOPPABLE"。
     b) motormaster_dash_unstoppable_vfx: 播放 move_status_unstoppable (周身金色光环与环形特效)。

2. [特殊技 2 - 大师级工艺 / A Master Craft]
   - 官方描述: "获得4秒的不可阻挡"
   - 实现方案:
     a) motormaster_sp2_unstoppable: 触发 onSpecial2Activate, 持续 4.0 秒, 作用于 self,
        赋予 unstoppable 霸体 buff, 呼出 "UNSTOPPABLE"。
     b) motormaster_sp2_unstoppable_vfx: 播放 move_status_unstoppable (周身金色光环与环形特效)。

【范围约束】：
用户明确指示：仅实现汽车大师的前冲和 SP2 后的 Unstoppable，其他能力暂不实现。
-----------------------------------------------------------------------------
"""

from ..core import make_unstoppable_statmod
from ..registry import register_bot

BOT_ID = "motormaster_gs_voyager2015"


@register_bot(BOT_ID, name_zh="汽车大师", desc="格斗系，前冲与SP2不可阻挡霸体")
def build_motormaster_abilities(base_hp: float = 34894.0, base_atk: float = 2629.0):
    """
    生成汽车大师专属能力修饰器。
    基准 5星50级 HP = 34894.0, ATK = 2629.0
    """
    mods = {}
    appears = {}
    buffs = {}

    # 1. 前冲霸体 (Dashing Unstoppable, 0.7s)
    m_dash, a_dash = make_unstoppable_statmod(
        mod_id="motormaster_dash_unstoppable",
        duration=0.7,
        trigger="onPlayerStateEnter",
        trigger_scope="state=Dash",
        appr_id="appr_motormaster_dash_unstoppable",
        callout_text="不可阻挡",
        show_callout=True,
        play_vfx=False,
    )
    mods.update(m_dash)
    appears.update(a_dash)

    # 2. SP2 4秒霸体 (Special Attack 2 Unstoppable, 4.0s)
    m_sp2, a_sp2 = make_unstoppable_statmod(
        mod_id="motormaster_sp2_unstoppable",
        duration=4.0,
        trigger="onSpecial2Activate",
        trigger_scope="",
        appr_id="appr_motormaster_sp2_unstoppable",
        callout_text="不可阻挡",
        show_callout=True,
        play_vfx=False,
    )
    mods.update(m_sp2)
    appears.update(a_sp2)

    return mods, appears, buffs
