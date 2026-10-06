#!/usr/bin/env python3
"""
Bot Ability Implementation: 救护车 (Ratchet)
===========================================
Bot ID: ratchet_gs_kabam
阵营: 汽车人 (Autobot) | 职业: 科技系 (Tech)

【官方技能真理源对照 (来自在线优先实现)】：
-----------------------------------------------------------------------------
1. [被动 - 远程震击 / Ranged Shock] (pua_icon: 0xe914)
   - 描述: "远程攻击+20%的暴击率，如果出暴击，将施加攻击力75%的震击伤害，持续6.5秒"
   - 实现方案:
     a) 天然属性修正: 远程暴击率 crit_chance_ranged = base_crit(0.15) + 0.20 = 0.35
        (作为角色天然常驻属性，不显示血条下方图标，不能被任何驱散效果移除)
     b) 远程暴击施加震击: make_shock_statmod(trigger="onCrit", trigger_scope="level=Ranged", chance=1.0, duration=6.5, total_dmg=0.75*ATK)

2. [SP3 - 震击 / Diagnostic Scan Shock] (pua_icon: 0xe914)
   - 描述: "100%概率施加震击，施加攻击力97.5%的震击伤害，持续4秒"
   - 实现方案: make_shock_statmod(trigger="onSpecial3Activate", chance=1.0, duration=4.0, total_dmg=0.975*ATK)
-----------------------------------------------------------------------------
"""

from ..core import make_shock_statmod
from ..registry import register_bot

BOT_ID = "ratchet_gs_kabam"


@register_bot(BOT_ID, name_zh="救护车", desc="科技系战地医师，天然远程高暴击、远程震击与诊断扫描震击")
def build_ratchet_abilities(base_hp: float = 28352.0, base_atk: float = 2029.0):
    """
    根据基准属性生成救护车全部专属能力修饰器。
    基准 5星50级 HP=28352, ATK = 2029.0
    """
    mods = {}
    appears = {}
    buffs = {}

    # 1. 战时远程暴击触发震击：持续 6.5 秒，总能量伤害 75% ATK (减益红)
    # (注：+20% 远程暴击率属于天然常驻属性，不在此处生成可驱散的临时 Buff)
    m_rb_shock, a_rb_shock = make_shock_statmod(
        mod_id="ratchet_ranged_shock",
        duration=6.5,
        total_dmg=float(round(base_atk * 0.75)),
        chance=1.0,
        trigger="onCrit",
        trigger_scope="level=Ranged",
        appr_id="appr_ratchet_ranged_shock",
        callout_text="震击",
        pua_icon="\uE914",
        color_hex="FF0000",
        gradient_bottom="FF0000",
    )
    mods.update(m_rb_shock)
    appears.update(a_rb_shock)

    # 2. SP3 诊断扫描震击：SP3 命中时 100% 几率施加 4 秒 97.5% ATK 震击 (减益红)
    m_sp3_shock, a_sp3_shock = make_shock_statmod(
        mod_id="ratchet_sp3_shock",
        duration=4.0,
        total_dmg=float(round(base_atk * 0.975)),
        chance=1.0,
        trigger="onSpecial3Hit",
        trigger_scope="",
        appr_id="appr_ratchet_sp3_shock",
        callout_text="震击",
        pua_icon="\uE914",
        color_hex="FF0000",
        gradient_bottom="FF0000",
    )
    mods.update(m_sp3_shock)
    appears.update(a_sp3_shock)

    return mods, appears, buffs
