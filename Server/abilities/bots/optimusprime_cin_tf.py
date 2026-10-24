#!/usr/bin/env python3
"""
Bot Ability Implementation: 电影擎天柱 (Optimus Prime MV1)
======================================================
Bot ID: optimusprime_cin_tf
阵营: 汽车人 (Autobot) | 职业: 格斗系 (Brawler)

【官方技能真理源对照 (来自 Upstash KV 聚合 Priorities 清单)】：
-----------------------------------------------------------------------------
1. [被动 - 护甲增益 / Armor Buff] (ID: 2724, pua_icon: 0xe517, category: passive)
   - 官方描述: "当进入格挡姿态时，有100%的概率获得护甲增益，降低受到攻击伤害的16.5%，持续7秒。"
   - 实现方案 (与 G1 擎天柱 optimus.py 完全对齐):
     optimusprime_cin_tf_block_armor:
       触发 onPlayerStateEnter, state=Block, 100% 概率获得 7.0 秒护甲增益 (减伤 16.5%),
       作用于 self, 蓝色血条圆环图标 (PUA: 0xe517), 呼出文字: "护甲"。

2. [被动 - 近战增益 / Melee Buff] (ID: 2725, pua_icon: 0xe412, category: passive)
   - 官方描述: "所有攻击：10%的概率获得近战增益，提升近战伤害60%，持续4秒。//最大一层，不可叠加，再次获得就刷新当前的"
   - 实现方案:
     optimusprime_cin_tf_melee_buff:
       触发 onHit, 10% 概率获得 4.0 秒近战增益 (+60% 近战伤害),
       作用于 self, 橙红血条圆环图标 (PUA: 0xe412), 呼出文字: "近战增益"。

3. [被动 - 意志力 / Willpower] (ID: 2726, pua_icon: 0xe942, category: passive)
   - 官方描述: "如果擎天柱正在流血状态，他将自己造成所有伤害的35%转化为自己的生命值。身上最多只能被施加一层流血，超过一层的流血会被当场净化，并转化为擎天柱最大能量的10%"
   - 实现方案:
     optimusprime_cin_tf_willpower:
       常驻被动 (trigger: always), 绿色圆环图标 (PUA: 0xe942),
       配合 Native C (skill_optimus_mv.c) 在流血时吸血回生 35% 伤害，并拦截第二层流血净化为 10% 能量。

4. [SP1 - 流血 / Bleed] (ID: 2713, pua_icon: 0xe401, category: sp1)
   - 官方描述: "60%概率施加流血，造成攻击力40%的伤害，持续4秒"
   - 实现方案 (与 Dinobot / Arcee 完全对齐):
     optimusprime_cin_tf_sp1_bleed:
       触发 onHit, level=Special1, 60% 概率施加 4.0 秒流血 (造成 40% ATK 伤害),
       作用于 opponent, 红色血条圆环图标 (PUA: 0xe401), 呼出文字: "流血"。

5. [SP1 - 伤害增益 / Dynamic Damage Boost] (ID: 2729, pua_icon: 0xe406, category: sp1)
   - 官方描述: "擎天柱失去体力越多，该技能伤害越高，最高增伤150% (50% HP 时增伤 75%)"
   - 实现方案:
     optimusprime_cin_tf_sp1_dynamic_boost:
       触发 onSpecial1Activate, 金色血条圆环图标 (PUA: 0xe406), 呼出文字: "伤害增益",
       配合 Native C (skill_optimus_mv.c) 依当前损失生命值动态增伤。

6. [SP2 - 双剑流血 / Guardian Slash Bleed] (ID: 2727, pua_icon: 0xe401, category: sp2)
   - 官方描述: "前两击每一击有90%概率施加流血，造成攻击力40%的伤害，持续4秒。"
   - 实现方案:
     optimusprime_cin_tf_sp2_bleed:
       触发 onHit, level=Special2;index=0,1 (前两击), 90% 概率施加 4.0 秒流血 (造成 40% ATK 伤害),
       作用于 opponent, 红色血条圆环图标 (PUA: 0xe401), 呼出文字: "流血"。
-----------------------------------------------------------------------------
"""

from ..core import (
    AbilityColor,
    make_statmod_appearance,
    make_condition_scope,
    make_armor_up_statmod,
    make_attack_boost_statmod,
    make_bleed_statmod,
    validate_color_code,
    validate_statmod,
)
from ..registry import register_bot

BOT_ID = "optimusprime_cin_tf"


@register_bot(BOT_ID, name_zh="电影擎天柱", desc="格斗系重装领袖，进入格挡获得护甲增益，攻击触发近战增益，意志力流血吸血与净化回能，SP1与SP2高额流血")
def build_optimusprime_cin_tf_abilities(base_hp: float = 29334.0, base_atk: float = 2398.0):
    mods = {}
    appears = {}

    # 1. 被动护甲增益 (ID: 2724): 进入格挡姿态 100% 获得 7s 护甲 (减伤 16.5%) - 与 G1 擎天柱完全对齐
    m_arm, a_arm = make_armor_up_statmod(
        mod_id="optimusprime_cin_tf_block_armor",
        duration=7.0,
        armor_bonus=0.165,
        chance=1.0,
        trigger="onPlayerStateEnter",
        trigger_scope="state=Block",
        appr_id="appr_optimusprime_cin_tf_block_armor",
        callout_text="护甲",
        show_callout=True,
        pua_icon="\uE517",
        color_hex="29EBF4",
        gradient_bottom="00C5E8",
        stackable=True,
        max_stacks=5,
    )
    mods.update(m_arm)
    appears.update(a_arm)

    # 2. 被动近战增益 (ID: 2725): 所有攻击 10% 概率触发 4s 近战增益 (+60% 近战伤害)
    m_atk, a_atk = make_attack_boost_statmod(
        mod_id="optimusprime_cin_tf_melee_buff",
        duration=4.0,
        attack_bonus=0.60,
        chance=0.10,
        trigger="onHit",
        trigger_scope="level=Light,Medium,Heavy",
        appr_id="appr_optimusprime_cin_tf_melee_buff",
        callout_text="近战增益",
        show_callout=True,
        pua_icon="\uE412",
        color_hex="F59E0B",
        gradient_bottom="D97706",
        stackable=False,
    )
    mods.update(m_atk)
    appears.update(a_atk)

    # 3. 被动意志力 (ID: 2726): 流血状态下造成的伤害 35% 转化为自身生命恢复，多余流血净化转 10% 能量
    validate_color_code("10B981", "willpower_tc")
    validate_color_code("059669", "willpower_gb")
    appr_willpower = {
        "id": "appr_optimusprime_cin_tf_willpower",
        "a": "意志力",
        "s": "意志力",
        "l": "流血状态下造成的伤害35%转化为自身生命恢复；最多存在一层流血，超出部分净化并转化为10%最大能量",
        "ss": "意志力吸血与流血净化回能",
        "t": "\uE942",
        "f": "",
        "st": "意志力",
        "ps": "意志力",
        "pl": "意志力生效中",
        "tc": "10B981",
        "gt": "10B981",
        "gb": "059669",
    }
    mod_willpower = {
        "id": "optimusprime_cin_tf_willpower",
        "t": "passive",
        "tm": "",
        "tr": ["always"],
        "uit": ["always"],
        "pri": 0,
        "trm": 0.0,
        "trs": make_condition_scope(self_status="dmg_bleed"),
        "trr": "repeat",
        "c": 1.0,
        "m": 0.35,
        "d": 0.0,
        "s": "none",
        "ta": "self",
        "mt": "passive",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "willpower",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_optimusprime_cin_tf_willpower"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_willpower)
    mods["optimusprime_cin_tf_willpower"] = mod_willpower
    appears["appr_optimusprime_cin_tf_willpower"] = appr_willpower

    # 3b. 意志力净化 Callout (ID: 2726b): 超过一层的流血1秒后被净化时弹出“净化”文字，绿色图标
    appr_purify = make_statmod_appearance(
        appr_id="appr_optimusprime_cin_tf_purify",
        callout_text="净化",
        desc="净化一层多余流血并转化为10%最大能量",
        short_desc="净化",
        pua_icon="\uE942",
        color=AbilityColor.GREEN_HEALTH,
        show_callout=True,
        active_desc="净化多余流血",
    )
    mod_purify = {
        "id": "optimusprime_cin_tf_purify",
        "t": "buff",
        "tm": "",
        "tr": [],
        "uit": [],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
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
        "g": "willpower_purify",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_optimusprime_cin_tf_purify"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_purify)
    mods["optimusprime_cin_tf_purify"] = mod_purify
    appears["appr_optimusprime_cin_tf_purify"] = appr_purify

    # 4. SP1 流血 (ID: 2713): 60% 几率施加流血 4 秒 (40% ATK 伤害) - 与 Dinobot / Arcee 对齐
    m_sp1_b, a_sp1_b = make_bleed_statmod(
        mod_id="optimusprime_cin_tf_sp1_bleed",
        duration=4.0,
        total_dmg=float(round(base_atk * 0.40)),
        chance=0.60,
        trigger="onHit",
        trigger_scope="level=Special1",
        appr_id="appr_optimusprime_cin_tf_sp1_bleed",
        callout_text="流血",
        buff_id="dmg_bleed",
    )
    mods.update(m_sp1_b)
    appears.update(a_sp1_b)

    # 5. SP1 伤害增益 (ID: 2729): 随失去生命值动态增伤，最高 +150% (50% HP 时增伤 75%)
    m_sp1_bst, a_sp1_bst = make_attack_boost_statmod(
        mod_id="optimusprime_cin_tf_sp1_dynamic_boost",
        duration=4.0,
        attack_bonus=1.50,
        chance=1.0,
        trigger="onSpecial1Activate",
        trigger_scope="",
        appr_id="appr_optimusprime_cin_tf_sp1_dynamic_boost",
        callout_text="伤害增益",
        show_callout=True,
        pua_icon="\uE406",
        color_hex="F59E0B",
        gradient_bottom="D97706",
        stackable=False,
    )
    mods.update(m_sp1_bst)
    appears.update(a_sp1_bst)

    # 6. SP2 流血 (ID: 2727): 前两击每一击 90% 概率施加流血 4 秒 (40% ATK 伤害)
    m_sp2_b, a_sp2_b = make_bleed_statmod(
        mod_id="optimusprime_cin_tf_sp2_bleed",
        duration=4.0,
        total_dmg=float(round(base_atk * 0.40)),
        chance=0.90,
        trigger="onHit",
        trigger_scope="level=Special2;index=0,1",
        appr_id="appr_optimusprime_cin_tf_sp2_bleed",
        callout_text="流血",
        buff_id="dmg_bleed",
    )
    mods.update(m_sp2_b)
    appears.update(a_sp2_b)

    return mods, appears
