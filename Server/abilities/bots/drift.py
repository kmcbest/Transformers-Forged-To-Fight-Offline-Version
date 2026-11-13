#!/usr/bin/env python3
"""
Bot Ability Implementation: 漂移 (Drift)
=======================================
Bot ID: drift_cin_aoe
阵营: 汽车人 (Autobot) | 职业: 格斗系 (Warrior)

【官方技能真理源对照 (来自 character_abilities 数据库)】：
-----------------------------------------------------------------------------
1. [被动 - 剑刃暴击] (ID: 2601, pua_icon: 0xe401, category: passive)
   - 官方描述: "近战与远程攻击出暴击时，有65%的概率造成攻击力30%的流血伤害，持续2秒。"
   - 实现方案:
     a) drift_sword_crit_bleed: 触发 onCrit，限制 level=Light,Medium,Heavy,Ranged，造成 30% ATK 流血伤害持续 2.0 秒。呼出文字: "流血"。

2. [被动 - 集中体系] (ID: 2602, pua_icon: 0xe40d, category: passive)
   - 官方描述: "连击数达到5次后漂移会获得精准增益，暴击几率提升35%，降低对手规避几率85%。重击命中可立即进入集中状态(直接获得5层)。"
   - 实现方案:
     b) drift_focus_crit_rate: 集中状态赋予 35% 暴击几率提升。
     c) 由 skill_drift.c 实时跟踪连击数与层数流转：
        - 1~4 击：黄色计数器图标
        - 5~9 击 (集中)：黄色精准图标，+35% 暴击率，降低对手 85% 规避率
        - 重击命中未达 5 击时直接获得 5 层集中！

3. [被动 - 中度集中] (ID: 2603, pua_icon: 0xe40d, category: passive)
   - 官方描述: "连击数达到10次后漂移会获得45%的暴击伤害增益。数字达到10的时候图标变蓝色，保留先前的暴击几率与克规避效果。"
   - 实现方案:
     d) drift_focus_crit_dmg: 中度集中提供 45% 暴击伤害加成。
     e) 由 skill_drift.c 控制 10 连击时切换为蓝色图标。

4. [觉醒 - 高度集中] (ID: 2604, pua_icon: 0xe40d, category: signature)
   - 官方描述: "连击数达到15次后漂移会达到完全集中，新施加的流血时长增加150%，直到被对手击中为止。达到15的时候变紫色，保留5次、10次增益。"
   - 实现方案:
     由 skill_drift.c 在达到 15 连击时将新流血持续时间延长 2.5x，并切换为紫色图标；受创后清零。

5. [被动 - 近战规避] (ID: 2605, pua_icon: 0xe509, category: passive)
   - 官方描述: "如果对方处于流血状态，漂移有10%的概率规避对手近战攻击。进入集中为15%，中度集中为20%，高度集中为25%。"
   - 实现方案:
     f) drift_evade_buff: 对方流血期间常驻绿色近战规避图标。
     g) 由 skill_drift.c 的 on_evade_check 动态判定 10% / 15% / 20% / 25% 规避几率。

6. [特殊技 1 - 流血] (ID: 2606, pua_icon: 0xe401, category: special_1)
   - 官方描述: "每一击85%的概率触发流血，造成攻击力45%的伤害，持续3秒。"
   - 实现方案:
     h) drift_sp1_bleed: 触发 onHit, level=Special1, 85% 概率造成 45% ATK 流血持续 3.0 秒。

7. [特殊技 2 - 流血] (ID: 2607, pua_icon: 0xe401, category: special_2)
   - 官方描述: "最后一击命中100%的概率触发流血，造成攻击力150%的伤害，持续10秒。"
   - 实现方案:
     i) drift_sp2_bleed: 触发 onHit, level=Special2 最后一击, 100% 概率造成 150% ATK 流血持续 10.0 秒。

8. [特殊技 3 - 流血] (ID: 2608, pua_icon: 0xe401, category: special_3)
   - 官方描述: "除最后一击外每击60%几率触发流血(30% ATK, 2秒)；最后一击100%几率触发流血(150% ATK, 10秒)。"
   - 实现方案:
     j) drift_sp3_bleed_multi: 特殊技3过程击 60% 几率 30% ATK 流血持续 2.0 秒。
     k) drift_sp3_bleed_finisher: 特殊技3终结击 100% 几率 150% ATK 流血持续 10.0 秒。
-----------------------------------------------------------------------------
"""

from ..core import (
    AbilityColor,
    make_bleed_statmod,
    make_crit_rate_statmod,
    make_crit_damage_statmod,
    make_evade_statmod,
    make_statmod_appearance,
    validate_statmod,
)
from ..registry import register_bot

BOT_ID = "drift_cin_aoe"


@register_bot(BOT_ID, name_zh="漂移", desc="格斗系剑圣，连击集中姿态、暴击流血与近战规避")
def build_drift_abilities(base_hp: float = 40154.0, base_atk: float = 3062.0):
    mods = {}
    appears = {}
    buffs = {}

    # -------------------------------------------------------------------------
    # 1. 剑刃暴击流血 (30% ATK 持续 2 秒, 65% 概率)
    # -------------------------------------------------------------------------
    m_sword_bleed, a_sword_bleed = make_bleed_statmod(
        mod_id="drift_sword_crit_bleed",
        duration=2.0,
        total_dmg=float(round(base_atk * 0.30, 2)),
        chance=0.65,
        trigger="onCrit",
        trigger_scope="level=Light,Medium,Heavy,Ranged",
        appr_id="appr_drift_sword_bleed",
        callout_text="流血",
        buff_id="dmg_bleed",
    )
    mods.update(m_sword_bleed)
    appears.update(a_sword_bleed)

    # -------------------------------------------------------------------------
    # 2. 集中状态外观与修饰器 (由 skill_drift.c 在 5/10/15 连击时动态控制)
    # -------------------------------------------------------------------------
    # a) 集中状态 (黄色 5 连击): +35% 暴击几率
    appr_focus_5 = make_statmod_appearance(
        appr_id="appr_drift_focus_yellow",
        callout_text="集中",
        desc="连击数达到5次后进入集中，暴击几率提高35%，克制对手规避。",
        short_desc="集中",
        pua_icon="\uE40D",
        color=AbilityColor.YELLOW_STATUS,
    )
    mod_focus_5 = {
        "id": "drift_focus_crit_rate",
        "t": "crit_rate",
        "tm": "",
        "tr": [],
        "uit": [],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.35,
        "d": -1.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 15,
        "g": "drift_focus",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_drift_focus_yellow"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_focus_5)
    mods["drift_focus_crit_rate"] = mod_focus_5
    appears["appr_drift_focus_yellow"] = appr_focus_5

    # b) 中度集中状态 (蓝色 10 连击): +45% 暴击伤害
    appr_focus_10 = make_statmod_appearance(
        appr_id="appr_drift_focus_blue",
        callout_text="中度集中",
        desc="连击数达到10次后进入中度集中，暴击伤害提升45%。",
        short_desc="中度集中",
        pua_icon="\uE40D",
        color=AbilityColor.BLUE_DEFENSE,
    )
    mod_focus_10 = {
        "id": "drift_focus_crit_dmg",
        "t": "crit_damage",
        "tm": "",
        "tr": [],
        "uit": [],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.45,
        "d": -1.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 15,
        "g": "drift_focus",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_drift_focus_blue"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_focus_10)
    mods["drift_focus_crit_dmg"] = mod_focus_10
    appears["appr_drift_focus_blue"] = appr_focus_10

    # c) 高度集中状态 (紫色 15 连击): 流血时长增加 150%
    appr_focus_15 = make_statmod_appearance(
        appr_id="appr_drift_focus_purple",
        callout_text="高度集中",
        desc="连击数达到15次后进入高度集中，新施加的流血时长增加150%。",
        short_desc="高度集中",
        pua_icon="\uE40D",
        color=AbilityColor.LIGHT_PURPLE_POWER,
    )
    mod_focus_15 = {
        "id": "drift_focus_bleed_boost",
        "t": "passive",
        "tm": "",
        "tr": [],
        "uit": [],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 1.50,
        "d": -1.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 15,
        "g": "drift_focus",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_drift_focus_purple"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_focus_15)
    mods["drift_focus_bleed_boost"] = mod_focus_15
    appears["appr_drift_focus_purple"] = appr_focus_15

    # -------------------------------------------------------------------------
    # 3. 近战规避常驻图标 (对手流血时激活)
    # -------------------------------------------------------------------------
    appr_evade = make_statmod_appearance(
        appr_id="appr_drift_evade",
        callout_text="规避",
        desc="对手处于流血状态时，漂移获得近战攻击规避能力。",
        short_desc="近战规避",
        pua_icon="\uE509",
        color=AbilityColor.GREEN_HEALTH,
    )
    mod_evade = {
        "id": "drift_evade_buff",
        "t": "modify_stat",
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
        "st": 1,
        "g": "drift_evade_display",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_drift_evade"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_evade)
    mods["drift_evade_buff"] = mod_evade
    appears["appr_drift_evade"] = appr_evade

    # -------------------------------------------------------------------------
    # 4. SP1 每击 85% 流血 (45% ATK 持续 3.0 秒)
    # -------------------------------------------------------------------------
    m_sp1_bleed, a_sp1_bleed = make_bleed_statmod(
        mod_id="drift_sp1_bleed",
        duration=3.0,
        total_dmg=float(round(base_atk * 0.45, 2)),
        chance=0.85,
        trigger="onHit",
        trigger_scope="level=Special1",
        appr_id="appr_drift_sp1_bleed",
        callout_text="流血",
        buff_id="dmg_bleed",
    )
    mods.update(m_sp1_bleed)
    appears.update(a_sp1_bleed)

    # -------------------------------------------------------------------------
    # 5. SP2 最后一击 100% 流血 (150% ATK 持续 10.0 秒)
    # -------------------------------------------------------------------------
    m_sp2_bleed, a_sp2_bleed = make_bleed_statmod(
        mod_id="drift_sp2_bleed",
        duration=10.0,
        total_dmg=float(round(base_atk * 1.50, 2)),
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Special2;lastHit=True",
        appr_id="appr_drift_sp2_bleed",
        callout_text="流血",
        buff_id="dmg_bleed",
    )
    mods.update(m_sp2_bleed)
    appears.update(a_sp2_bleed)

    # -------------------------------------------------------------------------
    # 6. SP3 过程击 60% 流血 (30% ATK 持续 2 秒) 与 终结击 100% 流血 (150% ATK, 10 秒)
    # -------------------------------------------------------------------------
    m_sp3_multi, a_sp3_multi = make_bleed_statmod(
        mod_id="drift_sp3_bleed_multi",
        duration=2.0,
        total_dmg=float(round(base_atk * 0.30, 2)),
        chance=0.60,
        trigger="onHit",
        trigger_scope="level=Special3;lastHit=False",
        appr_id="appr_drift_sp3_multi",
        callout_text="流血",
        buff_id="dmg_bleed",
    )
    mods.update(m_sp3_multi)
    appears.update(a_sp3_multi)

    m_sp3_fin, a_sp3_fin = make_bleed_statmod(
        mod_id="drift_sp3_bleed_finisher",
        duration=10.0,
        total_dmg=float(round(base_atk * 1.50, 2)),
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Special3;lastHit=True",
        appr_id="appr_drift_sp3_finisher",
        callout_text="流血",
        buff_id="dmg_bleed",
    )
    mods.update(m_sp3_fin)
    appears.update(a_sp3_fin)

    return mods, appears, buffs
