#!/usr/bin/env python3
"""
Bot Ability Implementation: 横炮 (Sideswipe)
===========================================
Bot ID: sideswipe_gs
阵营: 汽车人 (Autobot) | 职业: 侦察兵 (Scout)

【官方技能真理源对照 (来自 Upstash KV 聚合 Priorities 清单)】：
-----------------------------------------------------------------------------
1. [被动 - 近战规避受击蓄能] (ID: 2816, pua_icon: 0xe509, category: passive)
   - 官方描述: "受到7次普通攻击后，获得近战规避增益，38%的概率规避基础近战和SP1/SP2中的近战攻击，持续4秒。//显示一个灰色的规避图标，每次受到普通攻击计数加1，到7层变成带倒计时的绿色规避图标，特殊技中的攻击不计数"
   - 实现方案:
     sideswipe_evade_counter (灰色计数), sideswipe_melee_evade (绿色 38% 规避 4s)。

2. [被动 - 暴击率增益] (ID: 2820, pua_icon: 0xe40d, category: passive)
   - 官方描述: "横炮触发暴击时，100%概率得到一层3.8%的暴击率增益，可叠加。一旦横炮被击倒，就失去5层暴击率增益。"
   - 实现方案:
     sideswipe_crit_rate_stack: 触发 onCrit，叠加 3.8% 暴击率。

3. [被动 - 重击净化] (ID: 2822, category: passive)
   - 官方描述: "重击时净化所有震击增益"
   - 实现方案:
     sideswipe_heavy_cleanse_shock: 重击起手净化自身所有震击 (dmg_shock / shock)。

4. [被动 - 重击刷新] (ID: 2823, category: passive)
   - 官方描述: "重击时刷新所有暴击伤害增益的倒计时。"
   - 实现方案:
     sideswipe_heavy_refresh_crit_damage: 刷新暴伤增益倒计时。

5. [觉醒技 - 最大推力] (ID: 2824, pua_icon: 0xe403, category: signature)
   - 官方描述: "开局后得到一个能量获取增益，在12秒内得到最大能量的50%"
   - 实现方案:
     sideswipe_signature_max_thrust: 触发 onMatchStart / onStart，12 秒内获得 50% 最大能量 (150 点 Mana)。

6. [SP1 - 暴击几率] (ID: 2836, pua_icon: 0xe40d, category: sp1)
   - 官方描述: "本技能内+25.5%暴击率 //倒计时在技能结束后消失"
   - 实现方案:
     sideswipe_s1_crit_rate: 触发 onSpecial1Activate, 100% 概率获得 2.5 秒暴击几率加成 (+25.5%)。

7. [SP1 - 眩晕] (ID: 2825, pua_icon: 0xe605, category: sp1)
   - 官方描述: "//几拳就可以了，但用闪踢看起来更酷。 40%的概率击晕对手2.5秒"
   - 实现方案:
     sideswipe_s1_stun: 触发 onHit, level=Special1, 40% 概率击晕对手 2.5 秒。

8. [SP2 - 燃烧] (ID: 2834, pua_icon: 0xe41d, category: sp2)
   - 官方描述: "最后一击100%几率造成燃烧，施加攻击力80%的伤害，持续6秒。"
   - 实现方案:
     sideswipe_s2_burn: 触发 onHit, level=Special2, 100% 概率施加 6.0 秒燃烧 (80% ATK 伤害)。

9. [SP2 - 近战规避] (ID: 2838, pua_icon: 0xe509, category: sp2)
   - 官方描述: "获得8秒的近战规避，35%的概率规避基础近战和SP1/SP2中的近战攻击"
   - 实现方案:
     sideswipe_s2_melee_evade: 触发 onHit, level=Special2, 获得 8 秒 35% 近战规避增益。

10. [SP3 - 燃烧] (ID: 2835, pua_icon: 0xe41d, category: sp3)
    - 官方描述: "最后一击100%几率造成燃烧，施加攻击力100%的伤害，持续4秒。"
    - 实现方案:
      sideswipe_s3_burn: 触发 onHit, level=Special3, 100% 概率施加 4.0 秒燃烧 (100% ATK 伤害)。

11. [SP3 - 驱散] (ID: 2837, pua_icon: 0xe950, category: sp3)
    - 官方描述: "除最后一击外，每一击有60%的概率驱散对方一个增益"
    - 实现方案:
      sideswipe_s3_nullify: 触发 onHit, level=Special3, 60% 概率驱散对方 1 个增益。

12. [被动 - 闪避远程回能] (ID: 2839, category: passive)
    - 官方描述: "闪避远程普通攻击和远程重击时，1秒内获得最大能量的13%。"
    - 实现方案:
      sideswipe_evade_ranged_power: 闪避远程攻击获得 13% 能量 (39 点 Mana)。

13. [被动 - 闪避冲锋暴伤] (ID: 2840, pua_icon: 0xe406, category: passive)
    - 官方描述: "闪避对方前冲攻击时，获得暴击伤害增益，提升108%的暴击伤害，持续6秒"
    - 实现方案:
      sideswipe_evade_dash_crit_damage: 闪避冲锋时获得 108% 暴伤持续 6 秒。
-----------------------------------------------------------------------------
"""

from ..core import (
    AbilityColor,
    make_crit_rate_statmod,
    make_stun_statmod,
    make_burn_statmod,
    make_nullify_statmod,
    make_statmod_appearance,
    validate_statmod,
    validate_appear,
)
from ..registry import register_bot

BOT_ID = "sideswipe_gs"


@register_bot(BOT_ID, name_zh="横炮", desc="侦察兵迅捷突击手，受击近战规避、暴击率叠层、闪避远程回能与暴伤强化、SP1眩晕、SP2/SP3排气烈焰与驱散")
def build_sideswipe_abilities(base_hp: float = 26794.0, base_atk: float = 2698.0):
    mods = {}
    appears = {}
    buffs = {}

    # -------------------------------------------------------------------------
    # 1. SP1 暴击几率 (+25.5%, 持续 2.5 秒) (ID: 2836 - 既有保留)
    # -------------------------------------------------------------------------
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

    # -------------------------------------------------------------------------
    # 2. SP1 眩晕 (仅最后一击闪踢 40% 几率, 持续 2.5 秒) (ID: 2825 - 既有保留)
    # -------------------------------------------------------------------------
    m2, a2 = make_stun_statmod(
        mod_id="sideswipe_s1_stun",
        duration=2.5,
        chance=0.40,
        trigger="onHit",
        trigger_scope="level=Special1;dmgFlags=LastHit",
        callout_text="眩晕",
        pua_icon="\uE605",
    )
    mods.update(m2)
    appears.update(a2)

    # -------------------------------------------------------------------------
    # 3. SP2 燃烧 (仅最后一击 80% ATK: 2698 * 0.8 = 2158, 持续 6 秒, 100% 几率) (ID: 2834 - 既有保留)
    # -------------------------------------------------------------------------
    m3, a3 = make_burn_statmod(
        mod_id="sideswipe_s2_burn",
        duration=6.0,
        total_dmg=float(round(base_atk * 0.80)),
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Special2;dmgFlags=LastHit",
        callout_text="燃烧",
        stackable=True,
        pua_icon="\uE41D",
    )
    mods.update(m3)
    appears.update(a3)

    # -------------------------------------------------------------------------
    # 4. SP3 燃烧 (仅最后一击 100% ATK: 2698 * 1.0 = 2698, 持续 4 秒, 100% 几率) (ID: 2835 - 既有保留)
    # -------------------------------------------------------------------------
    m4, a4 = make_burn_statmod(
        mod_id="sideswipe_s3_burn",
        duration=4.0,
        total_dmg=float(round(base_atk * 1.00)),
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Special3;dmgFlags=LastHit",
        callout_text="燃烧",
        stackable=True,
        pua_icon="\uE41D",
    )
    mods.update(m4)
    appears.update(a4)

    # -------------------------------------------------------------------------
    # 5. SP3 驱散 (60% 几率驱散一个正面增益) (ID: 2837 - 既有保留)
    # -------------------------------------------------------------------------
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

    # =========================================================================
    # 以下为增量追加能力 (New Additions)
    # =========================================================================

    # -------------------------------------------------------------------------
    # 6. 受击蓄能与近战规避 (受到7次普通攻击触发，38%几率规避4秒) (ID: 2816)
    # -------------------------------------------------------------------------
    appr_evade_cnt = make_statmod_appearance(
        appr_id="appr_sideswipe_evade_counter",
        callout_text="规避蓄能",
        desc="受到普通攻击蓄能，达到7次时激活近战规避",
        pua_icon="\uE509",
        color=AbilityColor.GRAY_COOLDOWN,
        show_callout=False,
    )
    mod_evade_cnt = {
        "id": "sideswipe_evade_counter",
        "t": "crit_rate",
        "tm": "",
        "tr": [],
        "uit": [],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.0,
        "d": -1.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 7,
        "g": "counter_buff",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_sideswipe_evade_counter"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_evade_cnt)
    validate_appear(appr_evade_cnt)
    mods["sideswipe_evade_counter"] = mod_evade_cnt
    appears["appr_sideswipe_evade_counter"] = appr_evade_cnt

    appr_melee_evade = make_statmod_appearance(
        appr_id="appr_sideswipe_melee_evade",
        callout_text="近战规避",
        desc="激活近战规避，38%几率规避普通攻击与特殊技中的近战打击，持续4秒",
        pua_icon="\uE509",
        color=AbilityColor.GREEN_HEALTH,
        show_callout=True,
    )
    mod_melee_evade = {
        "id": "sideswipe_melee_evade",
        "t": "evade_melee",
        "tm": "",
        "tr": [],
        "uit": [],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.38,
        "d": 4.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "evade_buff",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_sideswipe_melee_evade"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_melee_evade)
    validate_appear(appr_melee_evade)
    mods["sideswipe_melee_evade"] = mod_melee_evade
    appears["appr_sideswipe_melee_evade"] = appr_melee_evade

    # -------------------------------------------------------------------------
    # 7. 暴击率增益叠层 (每次暴击+3.8%暴击率，被击倒失去5层) (ID: 2820)
    # -------------------------------------------------------------------------
    appr_crit_stack = make_statmod_appearance(
        appr_id="appr_sideswipe_crit_rate_stack",
        callout_text="暴击强化",
        desc="暴击获得3.8%暴击率增益，可叠加",
        pua_icon="\uE40D",
        color=AbilityColor.ORANGE_DAMAGE,
        show_callout=True,
    )
    mod_crit_stack = {
        "id": "sideswipe_crit_rate_stack",
        "t": "crit_rate",
        "tm": "",
        "tr": ["onCrit"],
        "uit": ["onCrit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.038,
        "d": 15.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 20,
        "g": "crit_rate_buff",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_sideswipe_crit_rate_stack"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_crit_stack)
    validate_appear(appr_crit_stack)
    mods["sideswipe_crit_rate_stack"] = mod_crit_stack
    appears["appr_sideswipe_crit_rate_stack"] = appr_crit_stack

    # -------------------------------------------------------------------------
    # 8. 觉醒技：最大推力 (开局12秒内获得最大能量的50%) (ID: 2824)
    # -------------------------------------------------------------------------
    appr_max_thrust = make_statmod_appearance(
        appr_id="appr_sideswipe_signature_max_thrust",
        callout_text="最大推力",
        desc="引擎全速超频！开局12秒内持续获得最大能量的50%",
        pua_icon="\uE606",
        color=AbilityColor.LIGHT_PURPLE_POWER,
        show_callout=True,
    )
    mod_max_thrust = {
        "id": "sideswipe_signature_max_thrust",
        "t": "power_gain",
        "tm": "",
        "tr": ["onStart"],
        "uit": ["onStart"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 450.0, # 50% 最大能量 (150 点 Mana = 1.5格, 450/3 = 150)
        "d": 12.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "power_gain_buff",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_sideswipe_signature_max_thrust"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_max_thrust)
    validate_appear(appr_max_thrust)
    mods["sideswipe_signature_max_thrust"] = mod_max_thrust
    appears["appr_sideswipe_signature_max_thrust"] = appr_max_thrust

    # -------------------------------------------------------------------------
    # 9. SP2 近战规避 (获得8秒近战规避，35%概率规避近战) (ID: 2838)
    # -------------------------------------------------------------------------
    appr_s2_evade = make_statmod_appearance(
        appr_id="appr_sideswipe_s2_melee_evade",
        callout_text="近战规避",
        desc="8秒内获得35%几率规避近战普通与特殊攻击",
        pua_icon="\uE509",
        color=AbilityColor.GREEN_HEALTH,
        show_callout=True,
    )
    mod_s2_evade = {
        "id": "sideswipe_s2_melee_evade",
        "t": "evade_melee",
        "tm": "",
        "tr": [],
        "uit": [],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.35,
        "d": 8.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "evade_buff",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_sideswipe_s2_melee_evade"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_s2_evade)
    validate_appear(appr_s2_evade)
    mods["sideswipe_s2_melee_evade"] = mod_s2_evade
    appears["appr_sideswipe_s2_melee_evade"] = appr_s2_evade

    # -------------------------------------------------------------------------
    # 10. 闪避远程回能 (闪避远程普通/重击时获得13%能量) (ID: 2839)
    # -------------------------------------------------------------------------
    appr_evade_pwr = make_statmod_appearance(
        appr_id="appr_sideswipe_evade_ranged_power",
        callout_text="能量获取",
        desc="闪避远程攻击获得13%最大能量",
        pua_icon="\uE608",
        color=AbilityColor.LIGHT_PURPLE_POWER,
        show_callout=True,
    )
    mod_evade_pwr = {
        "id": "sideswipe_evade_ranged_power",
        "t": "power_gain",
        "tm": "",
        "tr": [],
        "uit": [],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 39.0, # 13% 能量 (39 点 Mana)
        "d": 1.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "power_gain_buff",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_sideswipe_evade_ranged_power"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_evade_pwr)
    validate_appear(appr_evade_pwr)
    mods["sideswipe_evade_ranged_power"] = mod_evade_pwr
    appears["appr_sideswipe_evade_ranged_power"] = appr_evade_pwr

    # -------------------------------------------------------------------------
    # 11. 闪避冲锋暴击伤害 (+108% 暴击伤害持续 6 秒) (ID: 2840)
    # -------------------------------------------------------------------------
    appr_evade_dash = make_statmod_appearance(
        appr_id="appr_sideswipe_evade_dash_crit_damage",
        callout_text="暴伤强化",
        desc="闪避前冲攻击触发，暴击伤害提升108%，持续6秒",
        pua_icon="\uE906",
        color=AbilityColor.ORANGE_DAMAGE,
        show_callout=True,
    )
    mod_evade_dash = {
        "id": "sideswipe_evade_dash_crit_damage",
        "t": "crit_damage",
        "tm": "",
        "tr": [],
        "uit": [],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 1.08,
        "d": 6.0,
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
        "a": ["appr_sideswipe_evade_dash_crit_damage"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_evade_dash)
    validate_appear(appr_evade_dash)
    mods["sideswipe_evade_dash_crit_damage"] = mod_evade_dash
    appears["appr_sideswipe_evade_dash_crit_damage"] = appr_evade_dash

    return mods, appears, buffs
