#!/usr/bin/env python3
"""
Bot Ability Implementation: 倾天柱 (Optimus Prime SG)
=====================================================
Bot ID: optimusprime_sg_voyager2015
阵营: 汽车人 (Autobot) | 职业: 格斗系 (Brawler)

【官方技能真理源对照 (来自 character_abilities 数据库与 priority specs)】：
-----------------------------------------------------------------------------
1. [觉醒技 - 暴虐火种 / Spark of Tyranny] (ID: 3634, pua_icon: 0xe909, category: signature)
   - 官方描述: "所有特殊技发动时，获得一个概率充能，提升下一次特殊技无法防御的概率30%，直到特殊技触发无法防御时消耗掉。//未达100%时是紫色图标，达到100%时变为绿色图标。如果使用不可防御的SP1或SP2击中对手，则额外获得一层不可防御，下一次L1或M1必然不可防御，然后消耗掉。 //图标E41F"
   - 实现方案:
     a) optimusprime_sg_spark_charge: 特殊技启动获得暴虐火种充能，提高破防概率 (+30%/层, 上限4层, PUA: \uE909)。
     b) optimusprime_sg_unblockable_melee: 特殊技破防命中后，下一次轻/中攻击无法被格挡 (PUA: \uE41F)。

2. [被动 - 逆境暴发 / Struggle] (ID: 3642, pua_icon: 0xe406, category: passive)
   - 官方描述: "处于伤害减益状态时，攻击力提升50% //不会随伤害减益数量的增加而增加"
   - 实现方案:
     optimusprime_sg_struggle_attack_buff: 处于伤害减益状态时提升 50% 攻击力 (d=6.0, m=0.50, PUA: \uE406)。

3. [被动 - 减益控制 / Debuff Control] (ID: 3641, pua_icon: 0xe407, category: passive)
   - 官方描述: "被施加伤害减益时重击命中对手，可将所有伤害减益强度降低99%，但时间延长300%。"
   - 实现方案:
     optimusprime_sg_debuff_control: 重击命中对手获得 99% 伤害减免 (d=15.0, m=0.99, PUA: \uE407)。

4. [被动 - 减益循环 / Debuff Cycle] (ID: 3643, pua_icon: 0xe936, category: passive)
   - 官方描述: "自身处于流血状态时，所有攻击有10%的概率施加1层燃烧，造成攻击力70%的伤害，持续3秒，最大堆叠1层，可刷新
     自身处于燃烧状态时，所有攻击有10%的概率施加1层震击，造成攻击力70%的伤害，持续3秒，最大堆叠1层，可刷新
     自身处于震击状态时，所有攻击有10%的概率施加1层酸液，造成攻击力70%的伤害，持续3秒，最大堆叠1层，可刷新
     自身处于酸液状态时，所有攻击有10%的概率施加1层流血，造成攻击力70%的伤害，持续3秒，最大堆叠1层，可刷新"
   - 实现方案:
     a) optimusprime_sg_cycle_burn: 自身处于流血时，攻击 10% 概率施加 3 秒燃烧 (70% ATK, PUA: \uE41D)。
     b) optimusprime_sg_cycle_shock: 自身处于燃烧时，攻击 10% 概率施加 3 秒震击 (70% ATK, PUA: \uE914)。
     c) optimusprime_sg_cycle_acid: 自身处于震击时，攻击 10% 概率施加 3 秒酸液 (70% ATK, PUA: \uE936)。
     d) optimusprime_sg_cycle_bleed: 自身处于酸液时，攻击 10% 概率施加 3 秒流血 (70% ATK, PUA: \uE401)。
-----------------------------------------------------------------------------
"""

from ..core import (
    AbilityColor,
    make_statmod_appearance,
    make_armor_up_statmod,
    make_attack_boost_statmod,
    make_bleed_statmod,
    make_burn_statmod,
    make_shock_statmod,
    validate_statmod,
    validate_appear,
)
from ..registry import register_bot

BOT_ID = "optimusprime_sg_voyager2015"


@register_bot(BOT_ID, name_zh="倾天柱", desc="碎玻璃宇宙狂暴领袖，暴虐火种特殊技破防，逆境暴发减益增伤，减益控制与异常四重循环")
def build_optimusprime_sg_abilities(base_hp: float = 34850.0, base_atk: float = 3485.0):
    mods = {}
    appears = {}
    buffs = {
        "dmg_bleed": {
            "id": "dmg_bleed",
            "iconTexture": "",
            "image": "",
            "images3": False,
            "modeAvail": [],
            "scope": "global",
            "valueType": "absolute",
            "displayValue": float(round(base_atk * 0.70)),
            "c": 1,
            "value": float(round(base_atk * 0.70)),
            "buffType": "damage",
            "group": "dmg_bleed",
            "p": {"damage_type": "bleed"},
            "hasDuration": True,
            "e": 0,
            "time": {"amount": 3.0},
            "loc_name": "bleed",
            "loc_desc": "bleed",
        },
        "dmg_burn": {
            "id": "dmg_burn",
            "iconTexture": "",
            "image": "",
            "images3": False,
            "modeAvail": [],
            "scope": "global",
            "valueType": "absolute",
            "displayValue": float(round(base_atk * 0.70)),
            "c": 1,
            "value": float(round(base_atk * 0.70)),
            "buffType": "damage",
            "group": "dmg_burn",
            "p": {"damage_type": "burn"},
            "hasDuration": True,
            "e": 0,
            "time": {"amount": 3.0},
            "loc_name": "burn",
            "loc_desc": "burn",
        },
        "dmg_shock": {
            "id": "dmg_shock",
            "iconTexture": "",
            "image": "",
            "images3": False,
            "modeAvail": [],
            "scope": "global",
            "valueType": "absolute",
            "displayValue": float(round(base_atk * 0.70)),
            "c": 1,
            "value": float(round(base_atk * 0.70)),
            "buffType": "damage",
            "group": "dmg_shock",
            "p": {"damage_type": "shock"},
            "hasDuration": True,
            "e": 0,
            "time": {"amount": 3.0},
            "loc_name": "shock",
            "loc_desc": "shock",
        },
    }

    # =========================================================================
    # 1. 觉醒技 (Signature) - 暴虐火种 (ID: 3634)
    #    发动特殊技获得无法防御概率充能 (+30%/层，最多4层)
    #    特殊技破防命中后，下一次 L1/M1 必然无法防御
    # =========================================================================
    appr_spark = make_statmod_appearance(
        appr_id="appr_optimusprime_sg_spark",
        callout_text="暴虐火种",
        desc="特殊技破防概率充能 +30%",
        short_desc="暴虐火种",
        pua_icon="\uE909",
        color=AbilityColor.LIGHT_PURPLE_POWER,
        show_callout=True,
        active_desc="暴虐火种生效中",
    )
    appears["appr_optimusprime_sg_spark"] = appr_spark
    mod_spark = {
        "id": "optimusprime_sg_spark_charge",
        "t": "buff",
        "tm": "",
        "tr": ["onSpecial1Activate", "onSpecial2Activate", "onSpecial3Activate"],
        "uit": ["onSpecial1Activate", "onSpecial2Activate", "onSpecial3Activate"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.30,
        "d": -1.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 4,
        "g": "spark_tyranny",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_optimusprime_sg_spark"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_spark)
    mods["optimusprime_sg_spark_charge"] = mod_spark

    # 破防近战攻击
    appr_unbl_melee = make_statmod_appearance(
        appr_id="appr_optimusprime_sg_unblockable_melee",
        callout_text="无法防御",
        desc="下一次近战攻击无法防御",
        short_desc="无法防御",
        pua_icon="\uE41F",
        color=AbilityColor.ORANGE_DAMAGE,
        show_callout=True,
        active_desc="无法防御生效中",
    )
    appears["appr_optimusprime_sg_unblockable_melee"] = appr_unbl_melee
    mod_unbl_melee = {
        "id": "optimusprime_sg_unblockable_melee",
        "t": "buff",
        "tm": "",
        "tr": ["onHit"],
        "uit": ["onHit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "level=Special1,Special2",
        "trr": "repeat",
        "c": 1.0,
        "m": 1.0,
        "d": 8.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "unblockable",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_optimusprime_sg_unblockable_melee"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_unbl_melee)
    mods["optimusprime_sg_unblockable_melee"] = mod_unbl_melee

    # =========================================================================
    # 2. 战斗被动 - 逆境暴发 (ID: 3642)
    #    处于伤害减益状态时，攻击力提升 50%
    # =========================================================================
    m_struggle, a_struggle = make_attack_boost_statmod(
        mod_id="optimusprime_sg_struggle_attack_buff",
        duration=6.0,
        attack_bonus=0.50,
        chance=1.0,
        trigger="onDebuffReceived",
        trigger_scope="",
        appr_id="appr_optimusprime_sg_struggle",
        callout_text="逆境暴发",
        pua_icon="\uE406",
        color_hex=AbilityColor.ORANGE_DAMAGE_TC,
        gradient_bottom=AbilityColor.ORANGE_DAMAGE_GB,
        stackable=False,
        max_stacks=1,
    )
    mods.update(m_struggle)
    appears.update(a_struggle)

    # =========================================================================
    # 3. 战斗被动 - 减益控制 (ID: 3641)
    #    重击命中对手时，将自身所受伤害减益强度降低 99%，持续 15 秒
    # =========================================================================
    m_ctrl, a_ctrl = make_armor_up_statmod(
        mod_id="optimusprime_sg_debuff_control",
        duration=15.0,
        armor_bonus=0.99,
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Heavy",
        appr_id="appr_optimusprime_sg_debuff_ctrl",
        callout_text="减益控制",
        pua_icon="\uE407",
        color_hex=AbilityColor.BLUE_DEFENSE_TC,
        gradient_bottom=AbilityColor.BLUE_DEFENSE_GB,
        stackable=False,
        max_stacks=1,
    )
    mods.update(m_ctrl)
    appears.update(a_ctrl)

    # =========================================================================
    # 4. 战斗被动 - 减益循环 (ID: 3643)
    #    流血 -> 燃烧 -> 震击 -> 酸液 -> 流血 四重循环 (各 70% ATK, 3 秒, 10% 几率)
    # =========================================================================
    dot_cycle_dmg = float(round(base_atk * 0.70))

    # a) 自身流血时，所有攻击 10% 概率施加 3 秒燃烧
    m_burn, a_burn = make_burn_statmod(
        mod_id="optimusprime_sg_cycle_burn",
        duration=3.0,
        total_dmg=dot_cycle_dmg,
        chance=0.10,
        trigger="onHit",
        trigger_scope="self:debuff=bleed",
        appr_id="appr_optimusprime_sg_burn",
        callout_text="燃烧循环",
        pua_icon="\uE41D",
        stackable=False,
        max_stacks=1,
    )
    mods.update(m_burn)
    appears.update(a_burn)

    # b) 自身燃烧时，所有攻击 10% 概率施加 3 秒震击
    m_shock, a_shock = make_shock_statmod(
        mod_id="optimusprime_sg_cycle_shock",
        duration=3.0,
        total_dmg=dot_cycle_dmg,
        chance=0.10,
        trigger="onHit",
        trigger_scope="self:debuff=burn",
        appr_id="appr_optimusprime_sg_shock",
        callout_text="震击循环",
        pua_icon="\uE914",
        stackable=False,
        max_stacks=1,
    )
    mods.update(m_shock)
    appears.update(a_shock)

    # c) 自身震击时，所有攻击 10% 概率施加 3 秒酸液 (腐蚀伤害, 绿色 \uE936)
    m_acid, a_acid = make_burn_statmod(
        mod_id="optimusprime_sg_cycle_acid",
        duration=3.0,
        total_dmg=dot_cycle_dmg,
        chance=0.10,
        trigger="onHit",
        trigger_scope="self:debuff=shock",
        appr_id="appr_optimusprime_sg_acid",
        callout_text="酸液循环",
        pua_icon="\uE936",
        color_hex="10B981",
        gradient_bottom="059669",
        stackable=False,
        max_stacks=1,
    )
    mods.update(m_acid)
    appears.update(a_acid)

    # d) 自身酸液时，所有攻击 10% 概率施加 3 秒流血
    m_bleed, a_bleed = make_bleed_statmod(
        mod_id="optimusprime_sg_cycle_bleed",
        duration=3.0,
        total_dmg=dot_cycle_dmg,
        chance=0.10,
        trigger="onHit",
        trigger_scope="self:debuff=acid",
        appr_id="appr_optimusprime_sg_bleed",
        callout_text="流血循环",
        pua_icon="\uE401",
        stackable=False,
    )
    mods.update(m_bleed)
    appears.update(a_bleed)

    return mods, appears, buffs
