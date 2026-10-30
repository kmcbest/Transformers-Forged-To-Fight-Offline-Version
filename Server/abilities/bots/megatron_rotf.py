#!/usr/bin/env python3
"""
Bot Ability Implementation: 电影威震天 (Megatron ROTF)
=====================================================
Bot ID: megatron_cin_rotf
阵营: 霸天虎 (Decepticon) | 职业: 破坏系 (Demolition)

【官方技能真理源对照 (来自 character_abilities 数据库与 priority specs)】：
-----------------------------------------------------------------------------
1. [觉醒技 - 威震天万岁！/ All Hail Megaton!] (ID: 3107, pua_icon: 0xe90c, category: signature)
   - 官方描述: "威震天总会回来的。当生命值降至10%以下时，威震天将在3秒内恢复最大生命值的30%。//每局只触发一次，如果敌方的致命攻击一次性造成10%以上的伤害，该技能不触发，威震天直接被KO。"
   - 实现方案:
     megatron_rotf_sig_repair: 触发 onHealthThreshold (threshold=0.10), 3.0 秒内恢复 30% 最大生命值 (0.30 * base_hp)。呼出文字: "威震天万岁！", 图标: \uE90C。

2. [SP1 - 伤害电荷 / Impair Charge] (ID: 3108, pua_icon: 0xe81f, category: sp1)
   - 官方描述: "施加10层伤害电荷。"
   - 实现方案:
     megatron_rotf_sp1_impair_charge: 触发 onSpecial1Hit, 给对手施加 10 层伤害电荷 (d=-1.0, st=30, g=impair_charge, ta=opponent, mt=debuff)。呼出文字: "伤害电荷", 图标: \uE81F。

3. [SP2 - 远程增益 / Ranged Buff] (ID: 3109, pua_icon: 0xe41b, category: sp2)
   - 官方描述: "技能结束后，增加远程攻击速度和40%的远程伤害，持续6秒 // 不命中也可以"
   - 实现方案:
     megatron_rotf_sp2_ranged_boost: 触发 onSpecial2Activate, 提升 40% 远程伤害与 40% 射速，持续 6.0 秒。呼出文字: "远程增益", 图标: \uE41B。

4. [被动 - 天然护甲 / Permanent Armor] (ID: 3118, category: passive)
   - 官方描述: "+10%的永久护甲增益，无图标，不可被破甲移除"
   - 实现方案:
     megatron_rotf_passive_armor: 触发 onStart, 获得永久 +10% 护甲减伤 (d=-1.0, m=0.10, show_callout=False)。

5. [被动 - 不可阻挡 / Unstoppable] (ID: 3119, pua_icon: 0xe915, category: passive)
   - 官方描述: "当生命值降至80%/60%/40%时，获得不可阻挡增益，持续4秒"
   - 实现方案:
     megatron_rotf_hp_unstoppable: 触发 onHealthThreshold (threshold=0.80,0.60,0.40), 获得 4.0 秒不可阻挡状态。呼出文字: "不可阻挡", 图标: \uE915。

6. [被动 - 攻击增益 / Attack Buff] (ID: 3120, pua_icon: 0xe406, category: passive)
   - 官方描述: "如果在不可阻挡状态发动重击未命中，获得一个40%的攻击增益，持续10秒"
   - 实现方案:
     megatron_rotf_heavy_whiff_atk: 触发 onMiss (level=Heavy;self:state=Unstoppable), 获得 40% 攻击加成，持续 10.0 秒。呼出文字: "攻击增益", 图标: \uE406。

7. [被动 - 伤害电荷 / Impair Charge] (ID: 3121, pua_icon: 0xe81f, category: passive)
   - 官方描述: "所有攻击（含特殊技）命中时，给对手施加一层伤害电荷，出于重击和SP3消耗 //红色图标，无倒计时，可叠加"
   - 实现方案:
     megatron_rotf_hit_impair_charge: 触发 onHit, 命中给对手施加 1 层伤害电荷 (d=-1.0, st=30, g=impair_charge, ta=opponent, mt=debuff)。呼出文字: "伤害电荷", 图标: \uE81F。

8. [被动 - 电荷消耗 / Consume charges] (ID: 3122, pua_icon: 0xe404, category: passive)
   - 官方描述: "重击命中时，每1层伤害电荷增加5%的暴击几率。如果重击出暴击，将消耗所有的伤害电荷，每1层电荷增加2%的暴击伤害"
   - 实现方案:
     a) megatron_rotf_heavy_crit_boost: 触发 onHit (level=Heavy), 暴击几率提升 5%。呼出文字: "暴击提升", 图标: \uE404。
     b) megatron_rotf_heavy_crit_dmg: 触发 onCrit (level=Heavy), 暴击伤害提升 2%。呼出文字: "电荷消耗", 图标: \uE404。
     c) megatron_rotf_consume_charges: 触发 onCrit (level=Heavy), 移除对手所有伤害电荷。

9. [SP3 - 伤害电荷 / Impair Charge] (ID: 3123, pua_icon: 0xe81f, category: sp3)
   - 官方描述: "第一击施加20层伤害电荷。每1层伤害电荷增加5%的暴击几率。由于仅SP3施加的伤害电荷已将暴击几率拉满至100%，故最后一击必然暴击，每1层电荷增加2%的暴击伤害"
   - 实现方案:
     a) megatron_rotf_sp3_impair_charges: 触发 onSpecial3Hit (index=0), 给对手施加 20 层伤害电荷。
     b) megatron_rotf_sp3_crit_rate: 触发 onSpecial3Activate, 获得 100% 暴击率增益，持续 6.0 秒。
     c) megatron_rotf_sp3_crit_damage: 触发 onSpecial3Hit (dmgFlags=LastHit), 造成 +40% 暴击伤害加成。
-----------------------------------------------------------------------------
"""

from ..core import (
    AbilityColor,
    make_statmod_appearance,
    make_armor_up_statmod,
    make_attack_boost_statmod,
    make_crit_rate_statmod,
    make_crit_damage_statmod,
    make_heal_statmod,
    make_ranged_boost_statmod,
    make_unstoppable_statmod,
    validate_statmod,
    validate_appear,
)
from ..registry import register_bot

BOT_ID = "megatron_cin_rotf"


@register_bot(BOT_ID, name_zh="电影威震天", desc="霸天虎统帅，天然护甲与不可阻挡，重击消耗伤害电荷触发毁灭暴击与SP3核爆打击")
def build_megatron_rotf_abilities(base_hp: float = 34850.0, base_atk: float = 3485.0):
    mods = {}
    appears = {}
    buffs = {
        "heal": {
            "id": "heal",
            "iconTexture": "",
            "image": "",
            "images3": False,
            "modeAvail": [],
            "scope": "global",
            "valueType": "absolute",
            "displayValue": float(round(base_hp * 0.30)),
            "c": 1,
            "value": float(round(base_hp * 0.30)),
            "buffType": "heal",
            "group": "heal",
            "p": {},
            "hasDuration": True,
            "e": 0,
            "time": {"amount": 3.0},
            "loc_name": "heal",
            "loc_desc": "heal",
        }
    }

    # =========================================================================
    # 1. 觉醒技 (Signature) - 威震天万岁！ (ID: 3107)
    #    生命值跌破 10% 时，3 秒内修复恢复 30% 最大生命值
    # =========================================================================
    m_sig, a_sig = make_heal_statmod(
        mod_id="megatron_rotf_sig_repair",
        duration=3.0,
        heal_amount=float(round(base_hp * 0.30)),
        chance=1.0,
        trigger="onHealthThreshold",
        trigger_scope="threshold=0.10",
        appr_id="appr_megatron_rotf_repair",
        callout_text="威震天万岁！",
        pua_icon="\uE90C",
        color_hex=AbilityColor.GREEN_HEALTH_TC,
        gradient_bottom=AbilityColor.GREEN_HEALTH_GB,
        stackable=False,
        max_stacks=1,
    )
    mods.update(m_sig)
    appears.update(a_sig)

    # =========================================================================
    # 通用外观定义：伤害电荷 (Impair Charge, PUA: \uE81F, 减益红)
    # =========================================================================
    appr_impair = make_statmod_appearance(
        appr_id="appr_megatron_rotf_impair_charge",
        callout_text="伤害电荷",
        desc="受到伤害电荷影响，强化威震天重击与特殊技3",
        short_desc="伤害电荷",
        pua_icon="\uE81F",
        color=AbilityColor.RED_DEBUFF,
        show_callout=True,
        active_desc="受到伤害电荷影响",
    )
    appears["appr_megatron_rotf_impair_charge"] = appr_impair

    # =========================================================================
    # 2. 特殊技 1 (SP1) - 伤害电荷 (ID: 3108)
    #    SP1 命中施加 10 层伤害电荷
    # =========================================================================
    mod_sp1_impair = {
        "id": "megatron_rotf_sp1_impair_charge",
        "t": "attack_debuff",
        "tm": "",
        "tr": ["onSpecial1Hit"],
        "uit": ["onSpecial1Hit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 10.0,
        "d": -1.0,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 30,
        "g": "impair_charge",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_megatron_rotf_impair_charge"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_sp1_impair)
    mods["megatron_rotf_sp1_impair_charge"] = mod_sp1_impair

    # =========================================================================
    # 3. 特殊技 2 (SP2) - 远程增益 (ID: 3109)
    #    技能发动后增加 40% 远程射速与 40% 远程伤害，持续 6 秒
    # =========================================================================
    m_sp2, a_sp2 = make_ranged_boost_statmod(
        mod_id="megatron_rotf_sp2_ranged_boost",
        duration=6.0,
        damage_bonus=0.40,
        speed_bonus=0.40,
        trigger="onSpecial2Activate",
        trigger_scope="",
        appr_id="appr_megatron_rotf_sp2_ranged",
        callout_text="远程增益",
        pua_icon="\uE41B",
        color_hex=AbilityColor.ORANGE_DAMAGE_TC,
        gradient_bottom=AbilityColor.ORANGE_DAMAGE_GB,
    )
    mods.update(m_sp2)
    appears.update(a_sp2)

    # =========================================================================
    # 4. 常驻被动 - 天然护甲 (ID: 3118)
    #    +10% 永久护甲增益，无图标，不可被移除
    # =========================================================================
    m_armor, a_armor = make_armor_up_statmod(
        mod_id="megatron_rotf_passive_armor",
        duration=-1.0,
        armor_bonus=0.10,
        chance=1.0,
        trigger="onStart",
        trigger_scope="",
        appr_id="appr_megatron_rotf_armor",
        callout_text="天然护甲",
        show_callout=False,
        pua_icon="\uE517",
        color_hex=AbilityColor.BLUE_DEFENSE_TC,
        gradient_bottom=AbilityColor.BLUE_DEFENSE_GB,
        stackable=False,
        max_stacks=1,
    )
    mods.update(m_armor)
    appears.update(a_armor)

    # =========================================================================
    # 5. 战斗被动 - 不可阻挡 (ID: 3119)
    #    当生命值降至 80% / 60% / 40% 时获得 4 秒不可阻挡
    # =========================================================================
    m_unstopp, a_unstopp = make_unstoppable_statmod(
        mod_id="megatron_rotf_hp_unstoppable",
        duration=4.0,
        trigger="onHealthThreshold",
        trigger_scope="threshold=0.80,0.60,0.40",
        appr_id="appr_megatron_rotf_unstoppable",
        callout_text="不可阻挡",
        show_callout=True,
        play_vfx=True,
        pua_icon="\uE915",
        color_hex=AbilityColor.YELLOW_STATUS_TC,
    )
    mods.update(m_unstopp)
    appears.update(a_unstopp)

    # =========================================================================
    # 6. 战斗被动 - 攻击增益 (ID: 3120)
    #    不可阻挡状态下发动重击未命中，获得 40% 攻击加成持续 10 秒
    # =========================================================================
    m_atk, a_atk = make_attack_boost_statmod(
        mod_id="megatron_rotf_heavy_whiff_atk",
        duration=10.0,
        attack_bonus=0.40,
        chance=1.0,
        trigger="onMiss",
        trigger_scope="level=Heavy;self:state=Unstoppable",
        appr_id="appr_megatron_rotf_heavy_whiff_atk",
        callout_text="攻击增益",
        pua_icon="\uE406",
        color_hex=AbilityColor.ORANGE_DAMAGE_TC,
        gradient_bottom=AbilityColor.ORANGE_DAMAGE_GB,
        stackable=True,
        max_stacks=3,
    )
    mods.update(m_atk)
    appears.update(a_atk)

    # =========================================================================
    # 7. 战斗被动 - 所有攻击施加伤害电荷 (ID: 3121)
    #    命中给对手施加一层伤害电荷，无倒计时，可叠加至 30 层
    # =========================================================================
    mod_hit_impair = {
        "id": "megatron_rotf_hit_impair_charge",
        "t": "attack_debuff",
        "tm": "",
        "tr": ["onHit"],
        "uit": ["onHit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 1.0,
        "d": -1.0,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 30,
        "g": "impair_charge",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_megatron_rotf_impair_charge"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_hit_impair)
    mods["megatron_rotf_hit_impair_charge"] = mod_hit_impair

    # =========================================================================
    # 8. 战斗被动 - 电荷消耗与重击暴击提升 (ID: 3122)
    #    重击命中时每层增加 5% 暴击率；暴击时消耗全部电荷并增加暴击伤害
    # =========================================================================
    # a) 重击命中增加暴击几率
    m_h_crit, a_h_crit = make_crit_rate_statmod(
        mod_id="megatron_rotf_heavy_crit_boost",
        duration=1.0,
        crit_bonus=0.05,
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Heavy",
        appr_id="appr_megatron_rotf_crit_boost",
        callout_text="暴击提升",
        pua_icon="\uE404",
        color_hex=AbilityColor.ORANGE_DAMAGE_TC,
        gradient_bottom=AbilityColor.ORANGE_DAMAGE_GB,
    )
    mods.update(m_h_crit)
    appears.update(a_h_crit)

    # b) 重击暴击增加暴击伤害
    m_h_dmg, a_h_dmg = make_crit_damage_statmod(
        mod_id="megatron_rotf_heavy_crit_dmg",
        duration=1.0,
        crit_dmg_bonus=0.02,
        chance=1.0,
        trigger="onCrit",
        trigger_scope="level=Heavy",
        appr_id="appr_megatron_rotf_crit_dmg",
        callout_text="电荷消耗",
        pua_icon="\uE404",
        color_hex=AbilityColor.ORANGE_DAMAGE_TC,
        gradient_bottom=AbilityColor.ORANGE_DAMAGE_GB,
    )
    mods.update(m_h_dmg)
    appears.update(a_h_dmg)

    # c) 重击暴击消耗对手身上全部电荷
    appr_consume = make_statmod_appearance(
        appr_id="appr_megatron_rotf_consume_charges",
        callout_text="电荷爆发",
        desc="消耗所有伤害电荷",
        pua_icon="\uE404",
        color=AbilityColor.ORANGE_DAMAGE,
        show_callout=False,
    )
    appears["appr_megatron_rotf_consume_charges"] = appr_consume
    mod_consume = {
        "id": "megatron_rotf_consume_charges",
        "t": "remove",
        "tm": "megatron_rotf_hit_impair_charge",
        "tr": ["onCrit"],
        "uit": ["onCrit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "level=Heavy",
        "trr": "repeat",
        "c": 1.0,
        "m": 1.0,
        "d": 0.0,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_megatron_rotf_consume_charges"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_consume)
    mods["megatron_rotf_consume_charges"] = mod_consume

    # =========================================================================
    # 9. 特殊技 3 (SP3) - 伤害电荷与终极暴击 (ID: 3123)
    #    第一击施加 20 层伤害电荷，拉满暴击率并由最后一击造成暴击伤害
    # =========================================================================
    # a) 第一击施加 20 层伤害电荷
    mod_sp3_impair = {
        "id": "megatron_rotf_sp3_impair_charges",
        "t": "attack_debuff",
        "tm": "",
        "tr": ["onSpecial3Hit"],
        "uit": ["onSpecial3Hit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "index=0",
        "trr": "repeat",
        "c": 1.0,
        "m": 20.0,
        "d": -1.0,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 30,
        "g": "impair_charge",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_megatron_rotf_impair_charge"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_sp3_impair)
    mods["megatron_rotf_sp3_impair_charges"] = mod_sp3_impair

    # b) SP3 启动获得必杀暴击率 (+100% 暴击率)
    m_sp3_crit, a_sp3_crit = make_crit_rate_statmod(
        mod_id="megatron_rotf_sp3_crit_rate",
        duration=6.0,
        crit_bonus=1.00,
        chance=1.0,
        trigger="onSpecial3Activate",
        trigger_scope="",
        appr_id="appr_megatron_rotf_sp3_crit",
        callout_text="必杀暴击",
        pua_icon="\uE81F",
        color_hex=AbilityColor.ORANGE_DAMAGE_TC,
        gradient_bottom=AbilityColor.ORANGE_DAMAGE_GB,
    )
    mods.update(m_sp3_crit)
    appears.update(a_sp3_crit)

    # c) SP3 最后一击额外暴击伤害
    m_sp3_dmg, a_sp3_dmg = make_crit_damage_statmod(
        mod_id="megatron_rotf_sp3_crit_damage",
        duration=2.0,
        crit_dmg_bonus=0.40,
        chance=1.0,
        trigger="onSpecial3Hit",
        trigger_scope="dmgFlags=LastHit",
        appr_id="appr_megatron_rotf_sp3_dmg",
        callout_text="核爆重击",
        pua_icon="\uE81F",
        color_hex=AbilityColor.ORANGE_DAMAGE_TC,
        gradient_bottom=AbilityColor.ORANGE_DAMAGE_GB,
    )
    mods.update(m_sp3_dmg)
    appears.update(a_sp3_dmg)

    return mods, appears, buffs
