#!/usr/bin/env python3
"""
Bot Ability Implementation: 路障 (Barricade)
============================================
Bot ID: barricade_cin_dotm
阵营: 霸天虎 (Decepticon) | 职业: 格斗系 (Brawler)

【官方技能真理源对照 (来自 character_abilities / 网页待办 Priority 清单)】：
-----------------------------------------------------------------------------
1. [被动 - 近战规避 / Melee Evade] (ID: 2923, pua_icon: 0xe509, category: passive)
   - 官方描述: "被击倒时，有85%的概率获得3秒的近战规避，可规避基础近战和SP1/SP2中的近战攻击"
   - 实现方案:
     barricade_knockdown_evade_melee:
       触发 onPlayerStateEnter, state=Knockdown, 85% 概率获得 3.0 秒近战规避 buff,
       作用于 self, 绿色血条圆环图标 (PUA: 0xe509, Hex: 10B981 / 059669),
       呼出文字: "近战规避"。

2. [被动 - 远程规避 / Ranged Evade] (ID: 2935, pua_icon: 0xe518, category: passive)
   - 官方描述: "被击倒时，有85%的概率获得3秒的远程规避，可规避基础近战和SP1/SP2中的远程攻击"
   - 实现方案:
     barricade_knockdown_evade_ranged:
       触发 onPlayerStateEnter, state=Knockdown, 85% 概率获得 3.0 秒远程规避 buff,
       作用于 self, 绿色血条圆环图标 (PUA: 0xe518, Hex: 10B981 / 059669),
       呼出文字: "远程规避"。

3. [被动 - 暴击几率 / Critical Rate] (ID: 2936, pua_icon: 0xe406, category: passive)
   - 官方描述: "被击倒时，有40%的概率获得暴击几率增益，持续7.5秒"
   - 实现方案:
     barricade_knockdown_crit_rate:
       触发 onPlayerStateEnter, state=Knockdown, 40% 概率获得 7.5 秒暴击几率增益 buff (+30% 暴击率),
       作用于 self, 金色血条圆环图标 (PUA: 0xe406, Hex: F59E0B / D97706),
       呼出文字: "暴击几率"。
-----------------------------------------------------------------------------
"""

from ..core import make_evade_grant_statmod, make_crit_rate_statmod
from ..registry import register_bot

BOT_ID = "barricade_cin_dotm"


@register_bot(BOT_ID, name_zh="路障", desc="格斗系，被击倒起身触发近战规避、远程规避与暴击几率")
def build_barricade_abilities(base_hp: float = 30000.0, base_atk: float = 3000.0):
    """
    根据基准属性生成路障专属能力修饰器。
    官方设定：被击倒起身后，有概率获得近战规避 (85%, 3s)、远程规避 (85%, 3s) 与暴击几率增益 (40%, 7.5s)。
    触发机制：监听底层动画状态进入 onAnimStateEnter，目标动画为 StandupFromBack,StandupFromFront (起身)。
    """
    mods = {}
    appears = {}

    # 1. ID 2923: 被击倒起身后 85% 概率获得 3 秒近战规避 (受击时 85% 规避近战攻击)
    m_evade_melee, a_evade_melee = make_evade_grant_statmod(
        mod_id="barricade_knockdown_evade_melee",
        evade_type="melee",
        grant_chance=0.85,              # 85% 概率获得该增益
        evade_chance=0.85,              # 拥有增益时 85% 触发近战规避
        duration=3.0,                   # 起身后持续 3.0 秒
        trigger="onAnimStateEnter",
        trigger_scope="currAnim=StandupFromBack,StandupFromFront",
        appr_id="appr_barricade_knockdown_evade_melee",
        callout_text="近战规避",
        pua_icon="\uE509",
        color_hex="10B981",
        gradient_bottom="059669",
        show_callout=False,
    )
    mods.update(m_evade_melee)
    appears.update(a_evade_melee)

    # 2. ID 2935: 被击倒起身后 85% 概率获得 3 秒远程规避 (受击时 85% 规避远程攻击)
    m_evade_ranged, a_evade_ranged = make_evade_grant_statmod(
        mod_id="barricade_knockdown_evade_ranged",
        evade_type="ranged",
        grant_chance=0.85,              # 85% 概率获得该增益
        evade_chance=0.85,              # 拥有增益时 85% 触发远程规避
        duration=3.0,                   # 起身后持续 3.0 秒
        trigger="onAnimStateEnter",
        trigger_scope="currAnim=StandupFromBack,StandupFromFront",
        appr_id="appr_barricade_knockdown_evade_ranged",
        callout_text="远程规避",
        pua_icon="\uE518",
        color_hex="10B981",
        gradient_bottom="059669",
        show_callout=False,
    )
    mods.update(m_evade_ranged)
    appears.update(a_evade_ranged)

    # 3. ID 2936: 被击倒起身后 40% 概率获得 7.5 秒暴击几率增益 (+30% 暴击几率)
    m_crit, a_crit = make_crit_rate_statmod(
        mod_id="barricade_knockdown_crit_rate",
        duration=7.5,                   # 起身后持续 7.5 秒
        crit_bonus=0.30,
        chance=0.40,                    # 40% 概率获得该增益
        trigger="onAnimStateEnter",
        trigger_scope="currAnim=StandupFromBack,StandupFromFront",
        appr_id="appr_barricade_knockdown_crit_rate",
        callout_text="暴击几率",
        pua_icon="\uE406",
        color_hex="F59E0B",
        gradient_bottom="D97706",
    )
    mods.update(m_crit)
    appears.update(a_crit)

    return mods, appears


