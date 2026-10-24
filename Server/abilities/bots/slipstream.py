#!/usr/bin/env python3
"""
Bot Ability Implementation: 滑流 (Slipstream)
=============================================
Bot ID: slipstream_gs
阵营: 霸天虎 (Decepticon) | 职业: 侦察兵 (Scout)

【官方技能真理源对照 (来自 character_abilities 数据库)】：
-----------------------------------------------------------------------------
1. [被动 - 重击远程穿透] (ID: 3329)
   - 官方描述: "重击全程不会被远程普通攻击和远程重击击中。//对方的远程普通攻击和远程重击会直接从飞过，这个过程显示一个黄色的图标，重击完成后消失。"
   - 实现方案:
     slipstream_heavy_range_immune: 重击期间获得黄色穿透图标，子弹直接飞过。

2. [被动 - 暴击伤害] (ID: 3330)
   - 官方描述: "重击命中获得一个15%的暴击伤害增益，持续7秒"
   - 实现方案:
     slipstream_heavy_crit_damage: 触发 onHit，限制 level=Heavy，获得 15% 爆伤增益持续 7 秒。

3. [被动 - 远程驱散] (ID: 3332)
   - 官方描述: "基础远程攻击100%概率驱散对手一个护盾类增益"
   - 实现方案:
     slipstream_ranged_nullify_shield: 触发 onHit，限制 level=Ranged，100% 几率驱散护盾。

4. [被动 - 攻击增益] (ID: 3333)
   - 官方描述: "基础远程攻击有30%的概率得到20%的攻击增益，持续5秒"
   - 实现方案:
     slipstream_ranged_atk_buff: 触发 onHit，限制 level=Ranged，30% 几率获得 20% 攻击强化 5 秒。

5. [被动 - 净化并震击] (ID: 3335)
   - 官方描述: "M2命中时，净化自己所有震击减益，如果成功净化，向对手施加震击，造成攻击力60%的伤害，持续8秒。"
   - 实现方案:
     slipstream_m2_purify_shock: M2 命中触发，Native C 扫描并清除自身震击并反击对手 60% ATK 8 秒震击。

6. [被动 - 暴击几率] (ID: 3336)
   - 官方描述: "M2命中得到一个10%的暴击几率增益，持续6秒"
   - 实现方案:
     slipstream_m2_crit_buff: 触发 onHit，限制 level=Medium2，获得 10% 暴击率 6 秒。

7. [被动 - 背刺] (ID: 3338)
   - 官方描述: "暴击命中时，60%的概率施加背刺，对方每多一格能量，背刺概率增加12%。背刺图标在0.5秒内随机变为以下三个减益之一：
     1. 20%的暴击抗性减益，持续8秒 (图标E912)
     2. 30%的能量功率减益，持续8秒
     3. 逆火减益，持续8秒"
   - 实现方案:
     slipstream_backstab: 触发 onCrit，施加 0.5s 背刺前置，并在 Native C 转换为三选一减益。

8. [觉醒技 - 利用弱点] (ID: 3344)
   - 官方描述: "基础远程攻击和近战轻攻击（L1~L4）有50%的概率刷新对方身上最快要过期的1个减益。如果对方身上的减益少于4个，额外增加20%的概率。"
   - 实现方案:
     slipstream_signature_exploit: Native C 判定减益刷新机制。
-----------------------------------------------------------------------------
"""

from ..core import (
    AbilityColor,
    make_shock_statmod,
    make_statmod_appearance,
    make_condition_scope,
    validate_statmod,
    validate_appear,
    validate_color_code,
)
from ..registry import register_bot

BOT_ID = "slipstream_gs"


@register_bot(BOT_ID, name_zh="滑流", desc="侦察兵，重击远程穿透、远程驱盾与增益、M2反震击、高能背刺三态减益、觉醒弱点刷新")
def build_slipstream_abilities(base_hp: float = 32402.0, base_atk: float = 2306.0):
    """
    根据基准属性生成滑流专属全套能力修饰器。
    基准 5星50级 HP = 32402.0, ATK = 2306.0
    """
    mods = {}
    appears = {}
    buffs = {}

    # -------------------------------------------------------------------------
    # 1. 重击远程穿透 (Heavy Range Immune) (ID: 3329)
    # -------------------------------------------------------------------------
    appr_heavy_penetrate = make_statmod_appearance(
        appr_id="appr_slipstream_heavy_range_immune",
        callout_text="远程穿透",
        desc="重击过程中不受远程攻击伤害与硬直",
        pua_icon="\uE518",
        color=AbilityColor.YELLOW_STATUS,
        show_callout=True,
    )
    mod_heavy_penetrate = {
        "id": "slipstream_heavy_range_immune",
        "t": "evade_ranged",
        "tm": "",
        "tr": ["onHit"],
        "uit": ["onHit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "level=Heavy",
        "trr": "repeat",
        "c": 1.0,
        "m": 1.0,
        "d": 1.5,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "penetrate_buff",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_slipstream_heavy_range_immune"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_heavy_penetrate)
    validate_appear(appr_heavy_penetrate)
    mods["slipstream_heavy_range_immune"] = mod_heavy_penetrate
    appears["appr_slipstream_heavy_range_immune"] = appr_heavy_penetrate

    # -------------------------------------------------------------------------
    # 2. 重击暴击伤害增益 +15% 持续 7 秒 (ID: 3330)
    # -------------------------------------------------------------------------
    appr_heavy_crit_dmg = make_statmod_appearance(
        appr_id="appr_slipstream_heavy_crit_damage",
        callout_text="暴击伤害",
        desc="重击命中后暴击伤害提高15%，持续7秒",
        pua_icon="\uE406",
        color=AbilityColor.ORANGE_DAMAGE,
        show_callout=True,
    )
    mod_heavy_crit_dmg = {
        "id": "slipstream_heavy_crit_damage",
        "t": "crit_damage",
        "tm": "",
        "tr": ["onHit"],
        "uit": ["onHit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "level=Heavy",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.15,
        "d": 7.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "crit_damage_buff",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_slipstream_heavy_crit_damage"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_heavy_crit_dmg)
    validate_appear(appr_heavy_crit_dmg)
    mods["slipstream_heavy_crit_damage"] = mod_heavy_crit_dmg
    appears["appr_slipstream_heavy_crit_damage"] = appr_heavy_crit_dmg

    # -------------------------------------------------------------------------
    # 3. 基础远程攻击驱散对手护盾 (ID: 3332)
    # -------------------------------------------------------------------------
    appr_nullify_shield = make_statmod_appearance(
        appr_id="appr_slipstream_ranged_nullify_shield",
        callout_text="驱散护盾",
        desc="驱散对手防护力场与护盾增益",
        pua_icon="\uE950",
        color=AbilityColor.BLUE_DEFENSE,
        show_callout=True,
    )
    mod_nullify_shield = {
        "id": "slipstream_ranged_nullify_shield",
        "t": "nullify",
        "tm": "",
        "tr": ["onHit"],
        "uit": ["onHit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "level=Ranged",
        "trr": "repeat",
        "c": 1.0,
        "m": 1.0,
        "d": 0.5,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 0,
        "g": "nullify_debuff",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_slipstream_ranged_nullify_shield"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_nullify_shield)
    validate_appear(appr_nullify_shield)
    mods["slipstream_ranged_nullify_shield"] = mod_nullify_shield
    appears["appr_slipstream_ranged_nullify_shield"] = appr_nullify_shield

    # -------------------------------------------------------------------------
    # 4. 远程攻击 30% 几率 +20% 攻击增益 5 秒 (ID: 3333)
    # -------------------------------------------------------------------------
    appr_ranged_atk = make_statmod_appearance(
        appr_id="appr_slipstream_ranged_atk_buff",
        callout_text="攻击强化",
        desc="远程攻击触发，基础攻击力提升20%，持续5秒",
        pua_icon="\uE406",
        color=AbilityColor.ORANGE_DAMAGE,
        show_callout=True,
    )
    mod_ranged_atk = {
        "id": "slipstream_ranged_atk_buff",
        "t": "attack_buff",
        "tm": "",
        "tr": ["onHit"],
        "uit": ["onHit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "level=Ranged",
        "trr": "repeat",
        "c": 0.30,
        "m": 0.20,
        "d": 5.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "attack_buff",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_slipstream_ranged_atk_buff"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_ranged_atk)
    validate_appear(appr_ranged_atk)
    mods["slipstream_ranged_atk_buff"] = mod_ranged_atk
    appears["appr_slipstream_ranged_atk_buff"] = appr_ranged_atk

    # -------------------------------------------------------------------------
    # 5. M2 净化震击并反击对手 60% ATK 震击 8 秒 (ID: 3335)
    # -------------------------------------------------------------------------
    shock_dmg = float(round(base_atk * 0.60, 2))
    m_m2_shock, a_m2_shock = make_shock_statmod(
        mod_id="slipstream_m2_purify_shock",
        duration=8.0,
        total_dmg=shock_dmg,
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Medium2",
        appr_id="appr_slipstream_m2_shock",
        callout_text="震击反制",
        stackable=True,
    )
    mods.update(m_m2_shock)
    appears.update(a_m2_shock)

    # -------------------------------------------------------------------------
    # 6. M2 暴击几率 +10% 持续 6 秒 (ID: 3336)
    # -------------------------------------------------------------------------
    appr_m2_crit = make_statmod_appearance(
        appr_id="appr_slipstream_m2_crit_buff",
        callout_text="暴击强化",
        desc="M2命中后暴击率提高10%，持续6秒",
        pua_icon="\uE40D",
        color=AbilityColor.ORANGE_DAMAGE,
        show_callout=True,
    )
    mod_m2_crit = {
        "id": "slipstream_m2_crit_buff",
        "t": "crit_rate",
        "tm": "",
        "tr": ["onHit"],
        "uit": ["onHit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "level=Medium2",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.10,
        "d": 6.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "crit_rate_buff",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_slipstream_m2_crit_buff"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_m2_crit)
    validate_appear(appr_m2_crit)
    mods["slipstream_m2_crit_buff"] = mod_m2_crit
    appears["appr_slipstream_m2_crit_buff"] = appr_m2_crit

    # -------------------------------------------------------------------------
    # 7. 背刺前置 (Backstab) 0.5s 转化窗口 (ID: 3338)
    # -------------------------------------------------------------------------
    appr_backstab = make_statmod_appearance(
        appr_id="appr_slipstream_backstab",
        callout_text="背刺",
        desc="暴击触发背刺，即将转化为暴抗削弱、能量消耗或逆火减益",
        pua_icon="\uE604",
        color=AbilityColor.RED_DEBUFF,
        show_callout=True,
    )
    mod_backstab = {
        "id": "slipstream_backstab",
        "t": "decel",
        "tm": "",
        "tr": ["onCrit"],
        "uit": ["onCrit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 0.60,
        "m": 1.0,
        "d": 0.5,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "backstab_debuff",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_slipstream_backstab"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_backstab)
    validate_appear(appr_backstab)
    mods["slipstream_backstab"] = mod_backstab
    appears["appr_slipstream_backstab"] = appr_backstab

    # 背刺转化分支 1: 暴击抗性削弱 20% 8秒 (对方暴击率相对提高 20%)
    appr_crit_resist = make_statmod_appearance(
        appr_id="appr_slipstream_crit_resist_down",
        callout_text="易伤削弱",
        desc="对手暴击抗性降低20%，受暴击率提升，持续8秒",
        pua_icon="\uE912",
        color=AbilityColor.RED_DEBUFF,
        show_callout=True,
    )
    mod_crit_resist = {
        "id": "slipstream_crit_resist_down",
        "t": "crit_rate",
        "tm": "",
        "tr": ["onHit"],
        "uit": ["onHit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.20,
        "d": 8.0,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "resist_debuff",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_slipstream_crit_resist_down"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_crit_resist)
    validate_appear(appr_crit_resist)
    mods["slipstream_crit_resist_down"] = mod_crit_resist
    appears["appr_slipstream_crit_resist_down"] = appr_crit_resist

    # 背刺转化分支 2: 能量功率削弱 30% 8秒
    appr_power_drain = make_statmod_appearance(
        appr_id="appr_slipstream_power_drain",
        callout_text="能量损耗",
        desc="对手能量获取功率降低30%，持续8秒",
        pua_icon="\uE606",
        color=AbilityColor.RED_DEBUFF,
        show_callout=True,
    )
    mod_power_drain = {
        "id": "slipstream_power_drain",
        "t": "power_rate",
        "tm": "",
        "tr": ["onHit"],
        "uit": ["onHit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": -0.30,
        "d": 8.0,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "drain_debuff",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_slipstream_power_drain"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_power_drain)
    validate_appear(appr_power_drain)
    mods["slipstream_power_drain"] = mod_power_drain
    appears["appr_slipstream_power_drain"] = appr_power_drain

    # 背刺转化分支 3: 逆火减益 8秒 (对手释放特殊技时受到反噬伤害)
    appr_backfire = make_statmod_appearance(
        appr_id="appr_slipstream_backfire",
        callout_text="逆火",
        desc="对手释放特殊技时将遭受能量逆火反噬伤害，持续8秒",
        pua_icon="\uE918",
        color=AbilityColor.RED_DEBUFF,
        show_callout=True,
    )
    mod_backfire = {
        "id": "slipstream_backfire",
        "t": "dmg_burn",
        "tm": "",
        "tr": ["onHit"],
        "uit": ["onHit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": float(round(base_atk * 0.80, 2)),
        "d": 8.0,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "backfire_debuff",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_slipstream_backfire"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_backfire)
    validate_appear(appr_backfire)
    mods["slipstream_backfire"] = mod_backfire
    appears["appr_slipstream_backfire"] = appr_backfire

    # -------------------------------------------------------------------------
    # 8. 觉醒技：利用弱点 (Exploit Weakness) (ID: 3344)
    # -------------------------------------------------------------------------
    appr_exploit = make_statmod_appearance(
        appr_id="appr_slipstream_signature_exploit",
        callout_text="利用弱点",
        desc="轻击与远程有50%~70%概率刷新对手最快过期的减益",
        pua_icon="\uE40D",
        color=AbilityColor.ORANGE_DAMAGE,
        show_callout=True,
    )
    mod_exploit = {
        "id": "slipstream_signature_exploit",
        "t": "crit_rate",
        "tm": "",
        "tr": ["onHit"],
        "uit": ["onHit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "level=Light,Ranged",
        "trr": "repeat",
        "c": 0.50,
        "m": 0.05,
        "d": 1.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "exploit_buff",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_slipstream_signature_exploit"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_exploit)
    validate_appear(appr_exploit)
    mods["slipstream_signature_exploit"] = mod_exploit
    appears["appr_slipstream_signature_exploit"] = appr_exploit

    return mods, appears, buffs
