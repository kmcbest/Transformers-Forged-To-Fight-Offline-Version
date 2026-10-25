#!/usr/bin/env python3
"""
Bot Ability Implementation: 反冲 (Kickback)
===========================================
Bot ID: kickback_gs_kabam
阵营: 霸天虎 (Decepticon) | 职业: 侦察兵 (Scout)

【官方技能真理源对照 (来自 character_abilities 数据库)】：
-----------------------------------------------------------------------------
1. [被动 - 能量流失 / Power Leak] (ID: 3077)
   - 官方描述: "触发暴击时100%的概率造成能量流失，在10秒内扣除对方最大能量的9.6%，最多叠加5层。"
   - 实现方案:
     kickback_crit_power_leak: 暴击触发，施加持续 10 秒的能量流失 debuff，扣除 9.6% 能量，上限 5 层。

2. [被动 - 暴击几率 / Crit Rate on Kick] (ID: 3078)
   - 官方描述: "L4和M2命中时增加30%的暴击几率。//无图标，仅针对本次攻击本身"
   - 实现方案:
     kickback_crit_rate: L4 与 M2 攻击自身暴击率 +30%，由 Native C 结合判定。

3. [被动 - 能量功率 / Power Rate] (ID: 3080)
   - 官方描述: "对手处于能量流失状态时，反冲的近战攻击能量获取效率提升50%。"
   - 实现方案:
     kickback_power_rate: 配合 Native C，对手持有 power_leak 时近战命中能量增益 +50%。

4. [被动 - 近战规避 / Dash Evade] (ID: 3082)
   - 官方描述: "反冲的前冲攻击被对手闪避时，获得一个35%概率的近战规避增益，持续2秒。"
   - 实现方案:
     kickback_dash_evade: 获得 2 秒 35% 几率近战规避 buff (绿色图标)。

5. [被动 - 消耗(发起重击) / Heavy Start Cleanse] (ID: 3084)
   - 官方描述: "重击发起时，自己身上所有震击、能量汲取、能量锁定和能量功率减益都会被净化，每个被移除的减益都变为一层能量获取增益，2秒内获得其最大能量的3%。"
   - 实现方案:
     kickback_heavy_self_cleanse: 重击起手净化指定减益并转化为能量获取增益。

6. [被动 - 消耗(重击命中) / Heavy Hit Nullify] (ID: 3085)
   - 官方描述: "重击命中时，驱散对方身上所有能量功率和能量获取增益，每驱散一个，反冲得到一层能量获取增益，2秒内获得其最大能量的3%。"
   - 实现方案:
     kickback_heavy_enemy_nullify: 驱散对手能量增益并转化为自身能量获取。

7. [觉醒技 - T-齿轮破坏 / T-Cog Disrupt] (ID: 3088)
   - 官方描述: "重击命中有80%的概率破坏对手的变形齿轮，对手能量获取功率降低30%，持续10秒。//红色图标。如果对手此时使用重击，重击会失败且对手会眩晕2秒。"
   - 实现方案:
     kickback_tcog_disrupt: 红色图标，降低能量功率 30%，对手若放重击则反噬眩晕 2 秒。

8. [特殊技1 - 震击 / SP1 Shock] (ID: 3089)
   - 官方描述: "对于对方身上每1层能量流失，施加1层震击，造成攻击力40%的伤害，持续5秒。"
   - 实现方案:
     kickback_sp1_shock: 根据对手 power_leak 层数挂载对应层数震击。

9. [特殊技2 - 暴击几率、能量流失与流血 / SP2] (ID: 3090)
   - 官方描述:
     a) 技能命中时，获得一个30%的暴击率增益，持续8秒。
     b) 从第3击到最后一击，每一击触发暴击时100%的概率造成能量流失，在10秒内扣除对方最大能量的9.6%，最多叠加5层。
     c) 从第3击到最后一击，每一击暴击时100%的概率触发流血，造成攻击力26%的伤害，持续7秒。
   - 实现方案:
     kickback_sp2_crit_buff, kickback_sp2_power_leak, kickback_sp2_bleed。

10. [特殊技3 - 能量流失与修复 / SP3] (ID: 3091)
    - 官方描述:
      a) 技能所有攻击触发暴击时100%的概率造成能量流失，在10秒内扣除对方最大能量的9.6%，最多叠加5层。
      b) 对于对方身上每1层能量流失，反冲获得一个修复增益，5秒内修复最大生命值的3%。
    - 实现方案:
      kickback_sp3_power_leak, kickback_sp3_repair。
-----------------------------------------------------------------------------
"""

from ..core import (
    AbilityColor,
    make_bleed_statmod,
    make_shock_statmod,
    make_power_leak_statmod,
    make_statmod_appearance,
    make_condition_scope,
    validate_statmod,
    validate_appear,
    validate_color_code,
)
from ..registry import register_bot

BOT_ID = "kickback_gs_kabam"


@register_bot(BOT_ID, name_zh="反冲", desc="侦察兵，能量流失压制、重击净化与汲取、T-齿轮破坏重击反制、SP1流失转震击、SP3流失修复")
def build_kickback_abilities(base_hp: float = 32533.0, base_atk: float = 3880.0):
    """
    根据基准属性生成反冲专属全套能力修饰器。
    基准 5星50级 HP = 32533.0, ATK = 3880.0
    """
    mods = {}
    appears = {}
    buffs = {}

    # -------------------------------------------------------------------------
    # 1. 暴击能量流失 (Power Leak) 10.0s (ID: 3077)
    # 扣除对手 9.6% 能量 (0.096 * 300 = 28.8 点 Mana)
    # -------------------------------------------------------------------------
    m_leak, a_leak = make_power_leak_statmod(
        mod_id="kickback_crit_power_leak",
        duration=10.0,
        drain_bars=0.096,
        chance=1.0,
        trigger="onCrit",
        trigger_scope="",
        appr_id="appr_kickback_power_leak",
        callout_text="能量流失",
        pua_icon="\uE607",
        color_hex=AbilityColor.RED_DEBUFF_TC,
        gradient_bottom=AbilityColor.RED_DEBUFF_GB,
    )
    mods.update(m_leak)
    appears.update(a_leak)

    # -------------------------------------------------------------------------
    # 2. L4 与 M2 踢击暴击率 +30% (ID: 3078)
    # -------------------------------------------------------------------------
    appr_kick_crit = make_statmod_appearance(
        appr_id="appr_kickback_crit_rate",
        callout_text="暴击几率",
        desc="踢击命中时增加30%暴击率",
        pua_icon="\uE40D",
        color=AbilityColor.ORANGE_DAMAGE,
        show_callout=False,
    )
    mod_kick_crit = {
        "id": "kickback_crit_rate",
        "t": "crit_rate",
        "tm": "",
        "tr": ["onHit"],
        "uit": [],
        "pri": 0,
        "trm": 0.0,
        "trs": "level=Light4,Medium2",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.30,
        "d": 0.5,
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
        "a": ["appr_kickback_crit_rate"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_kick_crit)
    validate_appear(appr_kick_crit)
    mods["kickback_crit_rate"] = mod_kick_crit
    appears["appr_kickback_crit_rate"] = appr_kick_crit

    # -------------------------------------------------------------------------
    # 3. 能量功率 (Power Rate +50% on leaking opponent) (ID: 3080)
    # -------------------------------------------------------------------------
    appr_prate = make_statmod_appearance(
        appr_id="appr_kickback_power_rate",
        callout_text="能量功率",
        desc="对手处于能量流失状态时，近战攻击能量获取效率提升50%",
        pua_icon="\uE606",
        color=AbilityColor.LIGHT_PURPLE_POWER,
        show_callout=True,
    )
    mod_prate = {
        "id": "kickback_power_rate",
        "t": "power_rate",
        "tm": "",
        "tr": ["onHit"],
        "uit": ["onHit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "opp.status=power_leak",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.50,
        "d": 1.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "power_rate_buff",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_kickback_power_rate"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_prate)
    validate_appear(appr_prate)
    mods["kickback_power_rate"] = mod_prate
    appears["appr_kickback_power_rate"] = appr_prate

    # -------------------------------------------------------------------------
    # 4. 近战规避 35% 持续 2 秒 (ID: 3082)
    # -------------------------------------------------------------------------
    appr_dash_evade = make_statmod_appearance(
        appr_id="appr_kickback_dash_evade",
        callout_text="近战规避",
        desc="获得35%几率规避近战攻击",
        pua_icon="\uE509",
        color=AbilityColor.GREEN_HEALTH,
        show_callout=True,
    )
    mod_dash_evade = {
        "id": "kickback_dash_evade",
        "t": "evade_melee",
        "tm": "",
        "tr": ["onDodge"],
        "uit": ["onDodge"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 0.35,
        "m": 0.35,
        "d": 2.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "evade_melee_buff",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_kickback_dash_evade"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_dash_evade)
    validate_appear(appr_dash_evade)
    mods["kickback_dash_evade"] = mod_dash_evade
    appears["appr_kickback_dash_evade"] = appr_dash_evade

    # -------------------------------------------------------------------------
    # 5. 重击净化/汲取转化之能量获取增益 (ID: 3084, 3085)
    # 每层 2秒 获得最大能量 3% (0.03 * 300 = 9 点 Mana)
    # -------------------------------------------------------------------------
    appr_heavy_gain = make_statmod_appearance(
        appr_id="appr_kickback_heavy_power_gain",
        callout_text="能量获取",
        desc="2秒内获得最大能量的3%",
        pua_icon="\uE606",
        color=AbilityColor.LIGHT_PURPLE_POWER,
        show_callout=True,
    )
    mod_heavy_gain = {
        "id": "kickback_heavy_power_gain",
        "t": "power_gain",
        "tm": "",
        "tr": ["onHit"],
        "uit": ["onHit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 9.0,
        "d": 2.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 5,
        "g": "power_gain_buff",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_kickback_heavy_power_gain"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_heavy_gain)
    validate_appear(appr_heavy_gain)
    mods["kickback_heavy_power_gain"] = mod_heavy_gain
    appears["appr_kickback_heavy_power_gain"] = appr_heavy_gain

    # -------------------------------------------------------------------------
    # 6. 觉醒技：T-齿轮破坏 (T-Cog Disrupt) (ID: 3088)
    # 红色图标，降低能量获取功率 30%，持续 10 秒
    # -------------------------------------------------------------------------
    appr_tcog = make_statmod_appearance(
        appr_id="appr_kickback_tcog_disrupt",
        callout_text="T-齿轮破坏",
        desc="变形齿轮被破坏，能量获取功率降低30%，释放重击将失败并被眩晕2秒",
        pua_icon="\uE60F",
        color=AbilityColor.RED_DEBUFF,
        show_callout=True,
    )
    mod_tcog = {
        "id": "kickback_tcog_disrupt",
        "t": "power_rate",
        "tm": "",
        "tr": ["onHit"],
        "uit": ["onHit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "level=Heavy",
        "trr": "repeat",
        "c": 0.80,
        "m": -0.30,
        "d": 10.0,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "tcog_debuff",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_kickback_tcog_disrupt"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_tcog)
    validate_appear(appr_tcog)
    mods["kickback_tcog_disrupt"] = mod_tcog
    appears["appr_kickback_tcog_disrupt"] = appr_tcog

    # -------------------------------------------------------------------------
    # 7. SP1：震击 (每层流失施加 1 层 40% ATK 震击持续 5 秒) (ID: 3089)
    # -------------------------------------------------------------------------
    shock_dmg = float(round(base_atk * 0.40, 2))
    m_sp1_shock, a_sp1_shock = make_shock_statmod(
        mod_id="kickback_sp1_shock",
        duration=5.0,
        total_dmg=shock_dmg,
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Special1",
        appr_id="appr_kickback_sp1_shock",
        callout_text="震击",
        stackable=True,
    )
    mods.update(m_sp1_shock)
    appears.update(a_sp1_shock)

    # -------------------------------------------------------------------------
    # 8. SP2：30% 暴击率增益持续 8 秒 (ID: 3090)
    # -------------------------------------------------------------------------
    appr_sp2_crit = make_statmod_appearance(
        appr_id="appr_kickback_sp2_crit_buff",
        callout_text="暴击几率",
        desc="获得30%暴击率增益，持续8秒",
        pua_icon="\uE40D",
        color=AbilityColor.ORANGE_DAMAGE,
        show_callout=True,
    )
    mod_sp2_crit = {
        "id": "kickback_sp2_crit_buff",
        "t": "crit_rate",
        "tm": "",
        "tr": ["onHit"],
        "uit": ["onHit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "level=Special2",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.30,
        "d": 8.0,
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
        "a": ["appr_kickback_sp2_crit_buff"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_sp2_crit)
    validate_appear(appr_sp2_crit)
    mods["kickback_sp2_crit_buff"] = mod_sp2_crit
    appears["appr_kickback_sp2_crit_buff"] = appr_sp2_crit

    # -------------------------------------------------------------------------
    # 9. SP2：第3击到尾击暴击流血 26% ATK 持续 7 秒 (ID: 3090)
    # -------------------------------------------------------------------------
    sp2_bleed_dmg = float(round(base_atk * 0.26, 2))
    m_sp2_bleed, a_sp2_bleed = make_bleed_statmod(
        mod_id="kickback_sp2_bleed",
        duration=7.0,
        total_dmg=sp2_bleed_dmg,
        chance=1.0,
        trigger="onCrit",
        trigger_scope="level=Special2",
        appr_id="appr_kickback_sp2_bleed",
        callout_text="流血",
        stackable=True,
    )
    mods.update(m_sp2_bleed)
    appears.update(a_sp2_bleed)

    # -------------------------------------------------------------------------
    # 10. SP3：修复增益 (每层能量流失修复 3% HP 持续 5 秒) (ID: 3091)
    # -------------------------------------------------------------------------
    heal_amount = float(round(base_hp * 0.03, 2))
    appr_sp3_repair = make_statmod_appearance(
        appr_id="appr_kickback_sp3_repair",
        callout_text="修复",
        desc="5秒内修复最大生命值的3%",
        pua_icon="\uE401",
        color=AbilityColor.GREEN_HEALTH,
        show_callout=True,
    )
    mod_sp3_repair = {
        "id": "kickback_sp3_repair",
        "t": "heal",
        "tm": "",
        "tr": ["onHit"],
        "uit": ["onHit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "level=Special3",
        "trr": "repeat",
        "c": 1.0,
        "m": heal_amount,
        "d": 5.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 5,
        "g": "heal_buff",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_kickback_sp3_repair"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_sp3_repair)
    validate_appear(appr_sp3_repair)
    mods["kickback_sp3_repair"] = mod_sp3_repair
    appears["appr_kickback_sp3_repair"] = appr_sp3_repair

    return mods, appears, buffs
