#!/usr/bin/env python3
"""
Bot Ability Implementation: 幻影 (Mirage)
=========================================
Bot ID: mirage_gs_deluxe2016
阵营: 汽车人 (Autobot) | 职业: 侦察兵 (Scout)

【官方技能真理源对照 (来自 character_abilities 数据库与 priority specs)】：
-----------------------------------------------------------------------------
1. [觉醒技 - K.E.R.S / Kinetic Energy Recovery System] (ID: 2687, category: signature)
   - 官方描述: "发动不同特殊技得到不同的加成:
     特殊技1：远程攻击射速提升50%，持续19秒 // 橙图标 E41B
     特殊技2：近战攻击变得无法防御，持续19秒 // 橙图标 E41F
     特殊技3：获得90%的攻击加成，持续19秒 // 橙图标 E406
     //不管是否命中，都在发动瞬间得到加成"
   - 实现方案:
     a) mirage_kers_sp1_speed: 触发 onSpecial1Activate, 19.0 秒远程射速提升 50% (PUA: \uE41B)。
     b) mirage_kers_sp2_unblockable: 触发 onSpecial2Activate, 19.0 秒近战攻击无法防御 (PUA: \uE41F)。
     c) mirage_kers_sp3_atk: 触发 onSpecial3Activate, 19.0 秒攻击力提升 90% (PUA: \uE406)。

2. [SP1 - 破坏模式 / Disruption Mode] (ID: 2700, pua_icon: 0xe41b, category: sp1)
   - 官方描述: "进入破坏模式，该模式下远程攻击命中或被防有60%的概率扣除对方最大能量的9% // 紫色图标出现，无倒计时，并移除存在的失能模式和敏捷模式的图标"
   - 实现方案:
     a) mirage_mode_disruption: 触发 onSpecial1Activate, 获得破坏模式 (d=-1.0, PUA: \uE41B, 紫色)。
     b) 移除失能模式与敏捷模式。
     c) mirage_disrupt_drain_hit / block: 远程命中或被防 60% 概率扣除 9% 最大能量。

3. [SP2 - 失能模式 / Incapacitation Mode] (ID: 2701, pua_icon: 0xe41f, category: sp2)
   - 官方描述: "进入失能模式，该模式下近战攻击每一击能施加1层攻击减益，降低对方4.75%的攻击力，持续20秒，最多叠加15层 // 紫色E41F图标出现，无倒计时，并移除存在的破坏模式和敏捷模式的图标。攻击减益图标为e916，出现在对方侧。每施加7层攻击减益，眩晕对手1.5秒。"
   - 实现方案:
     a) mirage_mode_incapacitation: 触发 onSpecial2Activate, 获得失能模式 (d=-1.0, PUA: \uE41F, 紫色)。
     b) 移除破坏模式与敏捷模式。
     c) mirage_incap_atk_debuff: 近战攻击命中给对手施加 4.75% 攻击削弱，持续 20.0 秒，最多 15 层 (PUA: \uE916)。
     d) mirage_incap_stun: 近战命中概率眩晕对手 1.5 秒。

4. [SP3 - 敏捷模式 / Agility Mode] (ID: 2702, pua_icon: 0xe406, category: sp3)
   - 官方描述: "进入敏捷模式，每次极限闪避对方攻击时，获得15%的永久攻击增益，最大堆叠20层。 // 紫色E406图标出现，无倒计时，并移除存在的失能模式和破坏模式的图标。得到的攻击增益是橙色的E406图标，无倒计时，可叠加。"
   - 实现方案:
     a) mirage_mode_agility: 触发 onSpecial3Activate, 获得敏捷模式 (d=-1.0, PUA: \uE406, 紫色)。
     b) 移除破坏模式与失能模式。
     c) mirage_agility_atk_stack: 极限闪避触发获得 15% 永久攻击增益，最多 20 层 (d=-1.0, PUA: \uE406, 橙色)。

5. [被动 - 护盾 / Shield] (ID: 2703, pua_icon: 0xe515, category: passive)
   - 官方描述: "对方发动特殊技时得到一个护盾，降低对方90%的暴击伤害和远程伤害（包括特殊技中的远程攻击），直到幻影被击倒。"
   - 实现方案:
     a) mirage_special_shield: 触发 onSpecialActivate, 获得 90% 护盾减免直至被击倒 (PUA: \uE515)。
     b) mirage_shield_remove_on_kd: 被击倒时移除护盾。

6. [被动 - 能量涌动 / Power Flow] (ID: 2704, pua_icon: 0xe608, category: passive)
   - 官方描述: "幻影开局时进入能量模式，获得能量的功率提高30%，被击倒后退出能量模式，15秒后恢复 // 开局紫色图标，被击倒后变成灰色15秒倒计时图标，倒计时结束再变成紫色。"
   - 实现方案:
     a) mirage_power_flow: 触发 onStart, 获得能量获取提升 30% (d=-1.0, PUA: \uE608, 紫色)。
     b) 被击倒时移除并在 15 秒冷却后恢复。

7. [被动 - 重击远程穿透 / Heavy Range Immune] (ID: 2705, pua_icon: 0xe518, category: passive)
   - 官方描述: "重击全程不会被远程普通攻击和远程重击击中。//对方的远程普通攻击和远程重击会直接从幻影身边飞过，这个过程显示一个黄色的图标，重击完成后消失。"
   - 实现方案:
     mirage_heavy_range_evade: 进入 HeavyWindup / HeavyAttack 状态时获得 1.5 秒远程穿透规避 (PUA: \uE518, 黄色)。

8. [被动 - 重击净化 / Heavy Purify] (ID: 2706, category: passive)
   - 官方描述: "发动重击时净化所有燃烧伤害"
   - 实现方案:
     mirage_heavy_purify_burn: 发动重击时移除自身身上的燃烧状态。
-----------------------------------------------------------------------------
"""

from ..core import (
    AbilityColor,
    make_statmod_appearance,
    make_attack_boost_statmod,
    make_ranged_boost_statmod,
    make_power_leak_statmod,
    make_stun_statmod,
    make_evade_grant_statmod,
    make_remove_statmod,
    make_armor_up_statmod,
    validate_statmod,
    validate_appear,
)
from ..registry import register_bot

BOT_ID = "mirage_gs_deluxe2016"


@register_bot(BOT_ID, name_zh="幻影", desc="汽车人侦察兵，K.E.R.S 动能系统，三大战术模式切换，高额暴击与远程护盾")
def build_mirage_abilities(base_hp: float = 34850.0, base_atk: float = 3485.0):
    mods = {}
    appears = {}
    buffs = {}

    # =========================================================================
    # 1. 觉醒技 (Signature) - K.E.R.S (ID: 2687)
    # =========================================================================
    # a) 特殊技 1: 远程射速提升 50%，持续 19 秒 (橙图标 \uE41B)
    m_kers_sp1, a_kers_sp1 = make_ranged_boost_statmod(
        mod_id="mirage_kers_sp1_speed",
        duration=19.0,
        damage_bonus=0.0,
        speed_bonus=0.50,
        trigger="onSpecial1Activate",
        trigger_scope="",
        appr_id="appr_mirage_kers_sp1",
        callout_text="K.E.R.S",
        pua_icon="\uE41B",
        color_hex=AbilityColor.ORANGE_DAMAGE_TC,
        gradient_bottom=AbilityColor.ORANGE_DAMAGE_GB,
    )
    mods.update(m_kers_sp1)
    appears.update(a_kers_sp1)

    # b) 特殊技 2: 近战攻击不可防御，持续 19 秒 (橙图标 \uE41F)
    appr_kers_sp2 = make_statmod_appearance(
        appr_id="appr_mirage_kers_sp2",
        callout_text="无法防御",
        desc="近战攻击无法被格挡",
        short_desc="无法防御",
        pua_icon="\uE41F",
        color=AbilityColor.ORANGE_DAMAGE,
        show_callout=True,
        active_desc="无法防御生效中",
    )
    appears["appr_mirage_kers_sp2"] = appr_kers_sp2
    mod_kers_sp2 = {
        "id": "mirage_kers_sp2_unblockable",
        "t": "buff",
        "tm": "",
        "tr": ["onSpecial2Activate"],
        "uit": ["onSpecial2Activate"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 1.0,
        "d": 19.0,
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
        "a": ["appr_mirage_kers_sp2"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_kers_sp2)
    mods["mirage_kers_sp2_unblockable"] = mod_kers_sp2

    # c) 特殊技 3: 攻击加成 90%，持续 19 秒 (橙图标 \uE406)
    m_kers_sp3, a_kers_sp3 = make_attack_boost_statmod(
        mod_id="mirage_kers_sp3_atk",
        duration=19.0,
        attack_bonus=0.90,
        chance=1.0,
        trigger="onSpecial3Activate",
        trigger_scope="",
        appr_id="appr_mirage_kers_sp3",
        callout_text="K.E.R.S",
        pua_icon="\uE406",
        color_hex=AbilityColor.ORANGE_DAMAGE_TC,
        gradient_bottom=AbilityColor.ORANGE_DAMAGE_GB,
    )
    mods.update(m_kers_sp3)
    appears.update(a_kers_sp3)

    # =========================================================================
    # 2. 特殊技 1 (SP1) - 破坏模式 (ID: 2700)
    #    进入破坏模式，远程攻击命中或被防 60% 几率扣除 9% 最大能量
    # =========================================================================
    appr_mode_disrupt = make_statmod_appearance(
        appr_id="appr_mirage_mode_disrupt",
        callout_text="破坏模式",
        desc="破坏模式：远程攻击命中或被防扣除对手最大能量的9%",
        short_desc="破坏模式",
        pua_icon="\uE41B",
        color=AbilityColor.LIGHT_PURPLE_POWER,
        show_callout=True,
        active_desc="破坏模式已激活",
    )
    appears["appr_mirage_mode_disrupt"] = appr_mode_disrupt
    mod_mode_disrupt = {
        "id": "mirage_mode_disruption",
        "t": "buff",
        "tm": "",
        "tr": ["onSpecial1Activate"],
        "uit": ["onSpecial1Activate"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 1.0,
        "d": -1.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "mirage_mode",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_mirage_mode_disrupt"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_mode_disrupt)
    mods["mirage_mode_disruption"] = mod_mode_disrupt

    # 移除失能模式与敏捷模式
    m_rem_incap_sp1, a_rem_incap_sp1 = make_remove_statmod(
        mod_id="mirage_rem_incap_on_sp1",
        target_mod_id="mirage_mode_incapacitation",
        trigger="onSpecial1Activate",
        trigger_scope="",
        callout_text="切换模式",
        appr_id="appr_mirage_rem_incap_sp1",
        show_callout=False,
    )
    mods.update(m_rem_incap_sp1)
    appears.update(a_rem_incap_sp1)

    m_rem_agil_sp1, a_rem_agil_sp1 = make_remove_statmod(
        mod_id="mirage_rem_agil_on_sp1",
        target_mod_id="mirage_mode_agility",
        trigger="onSpecial1Activate",
        trigger_scope="",
        callout_text="切换模式",
        appr_id="appr_mirage_rem_agil_sp1",
        show_callout=False,
    )
    mods.update(m_rem_agil_sp1)
    appears.update(a_rem_agil_sp1)

    # 远程命中扣除能量
    m_dis_hit, a_dis_hit = make_power_leak_statmod(
        mod_id="mirage_disrupt_drain_hit",
        duration=0.5,
        drain_bars=0.27,
        chance=0.60,
        trigger="onHit",
        trigger_scope="level=Ranged",
        appr_id="appr_mirage_dis_drain_hit",
        callout_text="能量流失",
        pua_icon="\uE607",
    )
    mods.update(m_dis_hit)
    appears.update(a_dis_hit)

    # 远程被防扣除能量
    m_dis_blk, a_dis_blk = make_power_leak_statmod(
        mod_id="mirage_disrupt_drain_block",
        duration=0.5,
        drain_bars=0.27,
        chance=0.60,
        trigger="onBlocked",
        trigger_scope="level=Ranged",
        appr_id="appr_mirage_dis_drain_blk",
        callout_text="能量流失",
        pua_icon="\uE607",
    )
    mods.update(m_dis_blk)
    appears.update(a_dis_blk)

    # =========================================================================
    # 3. 特殊技 2 (SP2) - 失能模式 (ID: 2701)
    #    进入失能模式，近战攻击每击施加 4.75% 攻击减益 (20秒, 上限15层)
    #    施加攻击减益时附带眩晕对手 1.5 秒
    # =========================================================================
    appr_mode_incap = make_statmod_appearance(
        appr_id="appr_mirage_mode_incap",
        callout_text="失能模式",
        desc="失能模式：近战攻击施加攻击减益并眩晕对手",
        short_desc="失能模式",
        pua_icon="\uE41F",
        color=AbilityColor.LIGHT_PURPLE_POWER,
        show_callout=True,
        active_desc="失能模式已激活",
    )
    appears["appr_mirage_mode_incap"] = appr_mode_incap
    mod_mode_incap = {
        "id": "mirage_mode_incapacitation",
        "t": "buff",
        "tm": "",
        "tr": ["onSpecial2Activate"],
        "uit": ["onSpecial2Activate"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 1.0,
        "d": -1.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "mirage_mode",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_mirage_mode_incap"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_mode_incap)
    mods["mirage_mode_incapacitation"] = mod_mode_incap

    # 移除破坏模式与敏捷模式
    m_rem_dis_sp2, a_rem_dis_sp2 = make_remove_statmod(
        mod_id="mirage_rem_dis_on_sp2",
        target_mod_id="mirage_mode_disruption",
        trigger="onSpecial2Activate",
        trigger_scope="",
        callout_text="切换模式",
        appr_id="appr_mirage_rem_dis_sp2",
        show_callout=False,
    )
    mods.update(m_rem_dis_sp2)
    appears.update(a_rem_dis_sp2)

    m_rem_agil_sp2, a_rem_agil_sp2 = make_remove_statmod(
        mod_id="mirage_rem_agil_on_sp2",
        target_mod_id="mirage_mode_agility",
        trigger="onSpecial2Activate",
        trigger_scope="",
        callout_text="切换模式",
        appr_id="appr_mirage_rem_agil_sp2",
        show_callout=False,
    )
    mods.update(m_rem_agil_sp2)
    appears.update(a_rem_agil_sp2)

    # 施加攻击减益 (每层 4.75%，持续 20 秒，最多 15 层)
    appr_atk_debuff = make_statmod_appearance(
        appr_id="appr_mirage_atk_debuff",
        callout_text="攻击减益",
        desc="受到攻击减益，降低 4.75% 攻击力",
        short_desc="攻击削弱",
        pua_icon="\uE916",
        color=AbilityColor.RED_DEBUFF,
        show_callout=True,
        active_desc="攻击削弱生效中",
    )
    appears["appr_mirage_atk_debuff"] = appr_atk_debuff
    mod_atk_debuff = {
        "id": "mirage_incap_atk_debuff",
        "t": "attack_debuff",
        "tm": "",
        "tr": ["onHit"],
        "uit": ["onHit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "level=Light,Medium,Heavy",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.0475,
        "d": 20.0,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 15,
        "g": "attack_debuff",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_mirage_atk_debuff"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_atk_debuff)
    mods["mirage_incap_atk_debuff"] = mod_atk_debuff

    # 概率眩晕 (1.5 秒)
    m_incap_stun, a_incap_stun = make_stun_statmod(
        mod_id="mirage_incap_stun",
        duration=1.5,
        chance=0.143,
        trigger="onHit",
        trigger_scope="level=Light,Medium,Heavy",
        appr_id="appr_mirage_incap_stun",
        callout_text="眩晕",
        pua_icon="\uE605",
    )
    mods.update(m_incap_stun)
    appears.update(a_incap_stun)

    # =========================================================================
    # 4. 特殊技 3 (SP3) - 敏捷模式 (ID: 2702)
    #    进入敏捷模式，每次极限闪避获得 15% 永久攻击增益 (最多20层)
    # =========================================================================
    appr_mode_agility = make_statmod_appearance(
        appr_id="appr_mirage_mode_agility",
        callout_text="敏捷模式",
        desc="敏捷模式：极限闪避获得 15% 永久攻击增益",
        short_desc="敏捷模式",
        pua_icon="\uE406",
        color=AbilityColor.LIGHT_PURPLE_POWER,
        show_callout=True,
        active_desc="敏捷模式已激活",
    )
    appears["appr_mirage_mode_agility"] = appr_mode_agility
    mod_mode_agility = {
        "id": "mirage_mode_agility",
        "t": "buff",
        "tm": "",
        "tr": ["onSpecial3Activate"],
        "uit": ["onSpecial3Activate"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 1.0,
        "d": -1.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "mirage_mode",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_mirage_mode_agility"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_mode_agility)
    mods["mirage_mode_agility"] = mod_mode_agility

    # 移除破坏模式与失能模式
    m_rem_dis_sp3, a_rem_dis_sp3 = make_remove_statmod(
        mod_id="mirage_rem_dis_on_sp3",
        target_mod_id="mirage_mode_disruption",
        trigger="onSpecial3Activate",
        trigger_scope="",
        callout_text="切换模式",
        appr_id="appr_mirage_rem_dis_sp3",
        show_callout=False,
    )
    mods.update(m_rem_dis_sp3)
    appears.update(a_rem_dis_sp3)

    m_rem_incap_sp3, a_rem_incap_sp3 = make_remove_statmod(
        mod_id="mirage_rem_incap_on_sp3",
        target_mod_id="mirage_mode_incapacitation",
        trigger="onSpecial3Activate",
        trigger_scope="",
        callout_text="切换模式",
        appr_id="appr_mirage_rem_incap_sp3",
        show_callout=False,
    )
    mods.update(m_rem_incap_sp3)
    appears.update(a_rem_incap_sp3)

    # 极限闪避获得 15% 永久攻击加成 (无倒计时，可叠加至 20 层)
    m_agil_atk, a_agil_atk = make_attack_boost_statmod(
        mod_id="mirage_agility_atk_stack",
        duration=-1.0,
        attack_bonus=0.15,
        chance=1.0,
        trigger="onPlayerStateEnter",
        trigger_scope="state=EvadeMelee,EvadeRanged",
        appr_id="appr_mirage_agility_atk",
        callout_text="敏捷攻击",
        pua_icon="\uE406",
        color_hex=AbilityColor.ORANGE_DAMAGE_TC,
        gradient_bottom=AbilityColor.ORANGE_DAMAGE_GB,
        stackable=True,
        max_stacks=20,
    )
    mods.update(m_agil_atk)
    appears.update(a_agil_atk)

    # =========================================================================
    # 5. 战斗被动 - 护盾 (ID: 2703)
    #    对方发动特殊技时获得护盾，降低 90% 伤害，直到幻影被击倒
    # =========================================================================
    m_shield, a_shield = make_armor_up_statmod(
        mod_id="mirage_special_shield",
        duration=-1.0,
        armor_bonus=0.90,
        chance=1.0,
        trigger="onSpecialActivate",
        trigger_scope="",
        appr_id="appr_mirage_shield",
        callout_text="护盾",
        show_callout=True,
        pua_icon="\uE515",
        color_hex=AbilityColor.BLUE_DEFENSE_TC,
        gradient_bottom=AbilityColor.BLUE_DEFENSE_GB,
        stackable=False,
        max_stacks=1,
    )
    mods.update(m_shield)
    appears.update(a_shield)

    # 被击倒时移除护盾
    m_rem_shield, a_rem_shield = make_remove_statmod(
        mod_id="mirage_rem_shield_on_kd",
        target_mod_id="mirage_special_shield",
        trigger="onPlayerStateEnter",
        trigger_scope="state=Knockdown",
        callout_text="护盾破碎",
        appr_id="appr_mirage_rem_shield",
        show_callout=False,
    )
    mods.update(m_rem_shield)
    appears.update(a_rem_shield)

    # =========================================================================
    # 6. 战斗被动 - 能量涌动 (ID: 2704)
    #    开局能量功率提升 30%，被击倒后退出，15 秒后恢复
    # =========================================================================
    appr_power_flow = make_statmod_appearance(
        appr_id="appr_mirage_power_flow",
        callout_text="能量涌动",
        desc="能量涌动：能量获取功率提升 30%",
        short_desc="能量涌动",
        pua_icon="\uE608",
        color=AbilityColor.LIGHT_PURPLE_POWER,
        show_callout=True,
        active_desc="能量涌动生效中",
    )
    appears["appr_mirage_power_flow"] = appr_power_flow
    mod_power_flow = {
        "id": "mirage_power_flow",
        "t": "power_gain",
        "tm": "",
        "tr": ["onStart"],
        "uit": ["onStart"],
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
        "st": 1,
        "g": "power_flow",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_mirage_power_flow"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_power_flow)
    mods["mirage_power_flow"] = mod_power_flow

    # 被击倒移除能量涌动
    m_rem_pf, a_rem_pf = make_remove_statmod(
        mod_id="mirage_rem_power_flow_on_kd",
        target_mod_id="mirage_power_flow",
        trigger="onPlayerStateEnter",
        trigger_scope="state=Knockdown",
        callout_text="能量中断",
        appr_id="appr_mirage_rem_pf",
        show_callout=False,
    )
    mods.update(m_rem_pf)
    appears.update(a_rem_pf)

    # 15 秒冷却指示
    appr_pf_cd = make_statmod_appearance(
        appr_id="appr_mirage_power_flow_cd",
        callout_text="能量冷却",
        desc="能量涌动冷却中，15秒后恢复",
        short_desc="能量冷却",
        pua_icon="\uE608",
        color=AbilityColor.GRAY_COOLDOWN,
        show_callout=False,
        active_desc="能量涌动冷却中",
    )
    appears["appr_mirage_power_flow_cd"] = appr_pf_cd
    mod_pf_cd = {
        "id": "mirage_power_flow_cd",
        "t": "buff",
        "tm": "",
        "tr": ["onPlayerStateEnter"],
        "uit": ["onPlayerStateEnter"],
        "pri": 0,
        "trm": 0.0,
        "trs": "state=Knockdown",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.0,
        "d": 15.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "power_flow_cd",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_mirage_power_flow_cd"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_pf_cd)
    mods["mirage_power_flow_cd"] = mod_pf_cd

    # =========================================================================
    # 7. 战斗被动 - 重击远程穿透 (ID: 2705)
    #    重击全程不会被远程普通攻击和远程重击击中
    # =========================================================================
    m_heavy_evade, a_heavy_evade = make_evade_grant_statmod(
        mod_id="mirage_heavy_range_evade",
        evade_type="ranged",
        grant_chance=1.0,
        evade_chance=1.0,
        duration=1.5,
        trigger="onPlayerStateEnter",
        trigger_scope="state=HeavyWindup,HeavyAttack",
        appr_id="appr_mirage_range_evade",
        callout_text="远程穿透",
        pua_icon="\uE518",
        color_hex=AbilityColor.YELLOW_STATUS_TC,
        gradient_bottom=AbilityColor.YELLOW_STATUS_GB,
        show_callout=True,
    )
    mods.update(m_heavy_evade)
    appears.update(a_heavy_evade)

    # =========================================================================
    # 8. 战斗被动 - 重击净化 (ID: 2706)
    #    发动重击时净化所有燃烧伤害
    # =========================================================================
    m_purify, a_purify = make_remove_statmod(
        mod_id="mirage_heavy_purify_burn",
        target_mod_id="dmg_burn",
        trigger="onPlayerStateEnter",
        trigger_scope="state=HeavyWindup",
        callout_text="净化",
        appr_id="appr_mirage_purify",
        pua_icon="\uE508",
        color_hex=AbilityColor.WHITE_SPECIAL_TC,
        gradient_bottom=AbilityColor.WHITE_SPECIAL_GB,
        show_callout=True,
    )
    mods.update(m_purify)
    appears.update(a_purify)

    return mods, appears, buffs
