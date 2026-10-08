#!/usr/bin/env python3
"""
Bot Ability Implementation: 小黄蜂 (Bumblebee)
==============================================
Bot ID: bumblebee_gs_kabam
阵营: 汽车人 (Autobot) | 职业: 侦察兵 (Scout)

【官方技能真理源对照 (来自 character_abilities / 网页待办 Priority 清单)】：
-----------------------------------------------------------------------------
1. [被动 - 近战规避 / Melee Evade] (ID: 2439, pua_icon: 0xe509, category: passive)
   - 官方描述: "后闪会获得一个32%概率的近战规避，无倒计时，触发规避后消耗。"
   - 实现方案:
     bumblebee_dodge_evade_melee:
       触发 onPlayerStateEnter, state=Dodge (后闪触发), 32% 概率获得近战规避 buff (无倒计时, duration=-1.0),
       作用于 self, 绿色血条圆环图标 (PUA: 0xe509, Hex: 10B981 / 059669),
       呼出文字: "近战规避"。规避成功触发后消耗移除。
-----------------------------------------------------------------------------
"""

from ..core import make_evade_grant_statmod, make_evade_consume_statmod
from ..registry import register_bot

BOT_ID = "bumblebee_gs_kabam"


@register_bot(BOT_ID, name_zh="小黄蜂", desc="侦察兵，后闪获得32%概率消耗型近战规避")
def build_bumblebee_abilities(base_hp: float = 30000.0, base_atk: float = 3000.0):
    """
    根据基准属性生成小黄蜂专属能力修饰器。
    """
    mods = {}
    appears = {}

    # 1. 获得规避能力 (ID: 2439):
    # - 获得概率 grant_chance = 1.0 (后闪 100% 挂载规避 Buff 图标，血条下方常驻不限时)；
    # - 规避触发几率 evade_chance = 0.32 (受击时 32% 概率躲闪免伤，68% 不触发正常挨打且 Buff 保留)；
    # - 获得时 show_callout = False (后闪挂载时不弹大字)。
    m_grant, a_grant = make_evade_grant_statmod(
        mod_id="bumblebee_dodge_evade_melee",
        evade_type="melee",
        grant_chance=1.0,               # 获得概率 100%
        evade_chance=0.32,              # 触发规避几率 32%
        duration=0.0,                   # 无倒计时 (d = -1.0, 常驻直至被成功触发消耗)
        trigger="onPlayerStateEnter",
        trigger_scope="state=Dodge",    # 后闪触发
        appr_id="appr_bumblebee_dodge_evade_melee",
        callout_text="近战规避",
        pua_icon="\uE509",              # 近战规避矢量图标
        color_hex="10B981",             # 绿色
        gradient_bottom="059669",
        show_callout=False,             # 获得时不弹字
    )
    mods.update(m_grant)
    appears.update(a_grant)

    # 2. 规避成功触发后的消耗与呼出大字:
    # - 当 32% 规避命中时，客户端进入 EvadeMelee 免伤侧闪状态；
    # - 原生调用 Remove_BuffEffect 立即移除自身的 bumblebee_dodge_evade_melee；
    # - 同时头上呼出绿色大字 “规避”！
    m_consume, a_consume = make_evade_consume_statmod(
        mod_id="bumblebee_evade_consume",
        target_mod_id="bumblebee_dodge_evade_melee",
        evade_type="melee",
        callout_text="规避",
        appr_id="appr_bumblebee_evade_consume",
        pua_icon="\uE509",
        color_hex="10B981",
        gradient_bottom="059669",
        show_callout=True,
    )
    mods.update(m_consume)
    appears.update(a_consume)

    return mods, appears


