#!/usr/bin/env python3
"""
Bot Ability Implementation: 闹翻天 (Skywarp)
============================================
Bot ID: skywarp_gs_leader2015
阵营: 霸天虎 (Decepticon) | 职业: 战术系 (Tactician)

【官方技能真理源对照 (来自 tools/new_bots_priority_specs.json)】：
-----------------------------------------------------------------------------
1. [被动 - 传送充能 / Teleport Charge] (ID: 3323, pua_icon: 0xe98f, category: passive)
   - 官方描述: "每8秒得到一个传送充能，最大叠加3层  // 图标显示的方式参考暗天陨的充能
如果闹翻天受到暴击，有25%的概率丢失一个传送充能，受到战士系暴击时概率为50%
成功闪避一次特殊攻击，得到一个传送充能  // 多段连击的特殊攻击也只算一次"

2. [被动 - 特殊伤害减益 / Special Damage Debuff] (ID: 3324, pua_icon: 0xe41c, category: passive)
   - 官方描述: "普通远程攻击命中时有20%的概率施加1层特殊伤害减益，减少10%的特殊伤害，持续5秒 
远程重击命中时有50%的概率施加1层特殊伤害减益，减少10%的特殊伤害，持续9秒 
 // 可叠加，红图标"

3. [被动 - 传送攻击 / Teleport Attack] (ID: 3325, pua_icon: 0xe98f, category: passive)
   - 官方描述: "在拥有传送充能时，特殊攻击1和2会变为传送攻击  // 技能期间显示橙色图标，传送攻击会改变特殊技的动作，需要在asset中找到专属动作

传送攻击的暴击率增加27%
传送攻击不可防御
传送攻击有50%的概率施加8秒的能量锁定
传送攻击100%概率净化所有震击减益"

4. [特殊技 1 - 能量燃烧 / SP1 Power Burn] (ID: 3326, pua_icon: 0xe607, category: sp1)
   - 官方描述: "获得9秒能量燃烧状态，普通远程和远程重击命中或被防时立即扣除对手最大能量的8%   //黄图标"

5. [特殊技 2 - 修复阻止 / SP2 Repair Block] (ID: 3327, pua_icon: 0xe90c, category: sp2)
   - 官方描述: "最后一击命中时100%概率触发修复阻止，阻止对方所有回血能力，持续12秒"

6. [特殊技 3 - 能量窃取 / SP3 Power Steal] (ID: 3328, pua_icon: 0xe607, category: sp3)
   - 官方描述: "100%的概率窃取对手最大能量的50% //立即结算，我方加能量，对方减能量，红色图标出现在对方侧，一闪而过"

7. [特殊技 3 - 能量涌动 / SP3 Power Flow] (ID: 3329, pua_icon: 0xe608, category: sp3)
   - 官方描述: "如果能量窃取之后对方能量减为0，则得到一个永久能量涌动增益，提升能量功率15%，只能叠加一层。"
-----------------------------------------------------------------------------
"""

from ..core import (
    AbilityColor,
    make_power_lock_statmod,
    make_remove_statmod,
    make_statmod_appearance,
    validate_statmod,
    validate_appear,
    validate_color_code,
)
from ..registry import register_bot

BOT_ID = "skywarp_gs_leader2015"


@register_bot(BOT_ID, name_zh="闹翻天", desc="战术系瞬移刺客，空间折叠传送充能、致命传送突袭附带破防与能量锁定、特殊技火力压制、SP1高压能量燃烧、SP2永久禁疗与SP3巨量能量汲取")
def build_skywarp_abilities(base_hp: float = 34850.0, base_atk: float = 3485.0):
    """
    根据基准属性生成闹翻天全部专属能力修饰器。
    基准 5星50级 HP = 34850.0, ATK = 3485.0
    """
    mods = {}
    appears = {}
    buffs = {}

    # =========================================================================
    # 1. 通用外观 (StatModAppearances)
    # =========================================================================
    # 1.1 传送充能外观 (深紫色专属图标，参考暗天陨)
    appr_teleport_charge = make_statmod_appearance(
        appr_id="appr_skywarp_teleport_charge",
        callout_text="传送充能",
        desc="每8秒或成功闪避特殊技时获得1层传送充能，最多3层",
        pua_icon="\uE98F",
        color=AbilityColor.DARK_PURPLE_SPECIAL,
        show_callout=True,
    )
    validate_appear(appr_teleport_charge)
    appears[appr_teleport_charge["id"]] = appr_teleport_charge

    # 1.2 特殊伤害减益外观 (红色Debuff图标)
    appr_sp_dmg_debuff = make_statmod_appearance(
        appr_id="appr_skywarp_sp_dmg_debuff",
        callout_text="特殊削弱",
        desc="减少目标10%特殊攻击伤害，可叠加",
        pua_icon="\uE41C",
        color=AbilityColor.RED_DEBUFF,
        show_callout=True,
    )
    validate_appear(appr_sp_dmg_debuff)
    appears[appr_sp_dmg_debuff["id"]] = appr_sp_dmg_debuff

    # 1.3 传送攻击外观 (橙色增益图标)
    appr_teleport_attack = make_statmod_appearance(
        appr_id="appr_skywarp_teleport_attack",
        callout_text="传送攻击",
        desc="传送攻击暴击率+27%，不可防御，附带能量锁定与净化",
        pua_icon="\uE98F",
        color=AbilityColor.ORANGE_DAMAGE,
        show_callout=True,
    )
    validate_appear(appr_teleport_attack)
    appears[appr_teleport_attack["id"]] = appr_teleport_attack

    # 1.4 SP1 能量燃烧状态外观 (黄色状态图标)
    appr_sp1_power_burn = make_statmod_appearance(
        appr_id="appr_skywarp_sp1_power_burn",
        callout_text="能量燃烧",
        desc="获得9秒能量燃烧状态，远程命中或被防扣除对手最大能量的8%",
        pua_icon="\uE607",
        color=AbilityColor.YELLOW_STATUS,
        show_callout=True,
    )
    validate_appear(appr_sp1_power_burn)
    appears[appr_sp1_power_burn["id"]] = appr_sp1_power_burn

    # 1.5 SP2 修复阻止外观 (红色Debuff图标)
    appr_sp2_repair_block = make_statmod_appearance(
        appr_id="appr_skywarp_sp2_repair_block",
        callout_text="修复阻止",
        desc="阻止对方所有回血能力持续12秒",
        pua_icon="\uE90C",
        color=AbilityColor.RED_DEBUFF,
        show_callout=True,
    )
    validate_appear(appr_sp2_repair_block)
    appears[appr_sp2_repair_block["id"]] = appr_sp2_repair_block

    # 1.6 SP3 能量窃取外观 (红色Debuff瞬时图标)
    appr_sp3_power_steal = make_statmod_appearance(
        appr_id="appr_skywarp_sp3_power_steal",
        callout_text="能量窃取",
        desc="瞬间窃取对手最大能量的50%",
        pua_icon="\uE607",
        color=AbilityColor.RED_DEBUFF,
        show_callout=True,
    )
    validate_appear(appr_sp3_power_steal)
    appears[appr_sp3_power_steal["id"]] = appr_sp3_power_steal

    # 1.7 SP3 能量涌动外观 (浅紫色能量图标)
    appr_sp3_power_flow = make_statmod_appearance(
        appr_id="appr_skywarp_sp3_power_flow",
        callout_text="能量涌动",
        desc="永久提升能量获取功率15%",
        pua_icon="\uE608",
        color=AbilityColor.LIGHT_PURPLE_POWER,
        show_callout=True,
    )
    validate_appear(appr_sp3_power_flow)
    appears[appr_sp3_power_flow["id"]] = appr_sp3_power_flow

    # =========================================================================
    # 2. 被动能力：传送充能 (ID: 3323)
    # =========================================================================
    # 2.1 战斗开局及周期性获得传送充能，最多3层
    mod_teleport_start = {
        "id": "skywarp_teleport_charge_start",
        "t": "power",
        "tm": "",
        "tr": ["onStart"],
        "uit": ["onStart"],
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
        "st": 3,
        "g": "teleport_charge",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_skywarp_teleport_charge"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_teleport_start)
    mods[mod_teleport_start["id"]] = mod_teleport_start

    # 2.2 成功闪避特殊攻击获得1层传送充能
    mod_teleport_dodge = {
        "id": "skywarp_teleport_charge_dodge",
        "t": "power",
        "tm": "",
        "tr": ["onPlayerStateEnter"],
        "uit": ["onPlayerStateEnter"],
        "pri": 0,
        "trm": 0.0,
        "trs": "state=EvadeRanged,EvadeMelee,Dodge",
        "trr": "repeat",
        "c": 1.0,
        "m": 1.0,
        "d": -1.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 3,
        "g": "teleport_charge",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_skywarp_teleport_charge"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_teleport_dodge)
    mods[mod_teleport_dodge["id"]] = mod_teleport_dodge

    # =========================================================================
    # 3. 被动能力：特殊伤害减益 (ID: 3324)
    # =========================================================================
    # 3.1 普通远程命中: 20%概率施加1层特殊伤害减益(-10%)持续5秒
    mod_ranged_sp_debuff = {
        "id": "skywarp_ranged_sp_debuff",
        "t": "special_attack",
        "tm": "",
        "tr": ["onHit"],
        "uit": ["onHit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "level=Ranged",
        "trr": "repeat",
        "c": 0.20,
        "m": -0.10,
        "d": 5.0,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 10,
        "g": "special_dmg_debuff",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_skywarp_sp_dmg_debuff"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_ranged_sp_debuff)
    mods[mod_ranged_sp_debuff["id"]] = mod_ranged_sp_debuff

    # 3.2 远程重击命中: 50%概率施加1层特殊伤害减益(-10%)持续9秒
    mod_heavy_sp_debuff = {
        "id": "skywarp_heavy_sp_debuff",
        "t": "special_attack",
        "tm": "",
        "tr": ["onHit"],
        "uit": ["onHit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "level=Heavy",
        "trr": "repeat",
        "c": 0.50,
        "m": -0.10,
        "d": 9.0,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 10,
        "g": "special_dmg_debuff",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_skywarp_sp_dmg_debuff"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_heavy_sp_debuff)
    mods[mod_heavy_sp_debuff["id"]] = mod_heavy_sp_debuff

    # =========================================================================
    # 4. 被动能力：传送攻击增强与克制 (ID: 3325)
    # =========================================================================
    # 4.1 传送攻击暴击率增加27%
    mod_teleport_crit = {
        "id": "skywarp_teleport_crit_rate",
        "t": "crit_rate",
        "tm": "",
        "tr": ["onSpecial1Activate", "onSpecial2Activate"],
        "uit": ["onSpecial1Activate", "onSpecial2Activate"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.27,
        "d": 4.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "crit_rate",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_skywarp_teleport_attack"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_teleport_crit)
    mods[mod_teleport_crit["id"]] = mod_teleport_crit

    # 4.2 传送攻击不可防御 (Unblockable)
    mod_teleport_unblockable = {
        "id": "skywarp_teleport_unblockable",
        "t": "unblockable",
        "tm": "",
        "tr": ["onSpecial1Activate", "onSpecial2Activate"],
        "uit": ["onSpecial1Activate", "onSpecial2Activate"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 1.0,
        "d": 4.0,
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
        "a": ["appr_skywarp_teleport_attack"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_teleport_unblockable)
    mods[mod_teleport_unblockable["id"]] = mod_teleport_unblockable

    # 4.3 传送攻击50%概率施加8秒能量锁定
    m_tele_lock, a_tele_lock = make_power_lock_statmod(
        mod_id="skywarp_teleport_power_lock",
        duration=8.0,
        chance=0.50,
        trigger="onHit",
        trigger_scope="level=Special1,Special2",
        appr_id="appr_skywarp_power_lock",
        callout_text="能量锁定",
        pua_icon="\uE523",
    )
    mods.update(m_tele_lock)
    appears.update(a_tele_lock)

    # 4.4 传送攻击100%概率净化所有震击减益
    m_cleanse, a_cleanse = make_remove_statmod(
        mod_id="skywarp_cleanse_shock",
        target_mod_id="dmg_shock",
        trigger="onSpecialActivate",
        trigger_scope="level=Special1,Special2",
        callout_text="净化",
        appr_id="appr_skywarp_cleanse",
        pua_icon="\uE509",
        color_hex="10B981",
        gradient_bottom="059669",
    )
    mods.update(m_cleanse)
    appears.update(a_cleanse)

    # =========================================================================
    # 5. 特殊技 1 (SP1): 能量燃烧 (ID: 3326)
    # =========================================================================
    # 5.1 SP1 激活获得9秒能量燃烧状态
    mod_sp1_burn_state = {
        "id": "skywarp_sp1_burn_state",
        "t": "power_burn",
        "tm": "",
        "tr": ["onSpecial1Activate"],
        "uit": ["onSpecial1Activate"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 1.0,
        "d": 9.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "power_burn_state",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_skywarp_sp1_power_burn"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_sp1_burn_state)
    mods[mod_sp1_burn_state["id"]] = mod_sp1_burn_state

    # 5.2 状态期间普通远程和远程重击命中扣除对手最大能量的8% (72 Mana)
    mod_sp1_burn_drain = {
        "id": "skywarp_sp1_burn_drain",
        "t": "power_gain",
        "tm": "",
        "tr": ["onHit"],
        "uit": ["onHit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "level=Ranged,Heavy",
        "trr": "repeat",
        "c": 1.0,
        "m": -72.0,
        "d": 0.5,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 10,
        "g": "power_burn_drain",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_skywarp_sp1_power_burn"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_sp1_burn_drain)
    mods[mod_sp1_burn_drain["id"]] = mod_sp1_burn_drain

    # =========================================================================
    # 6. 特殊技 2 (SP2): 修复阻止 (ID: 3327)
    # =========================================================================
    # 最后一击命中100%触发修复阻止，阻止对方所有回血能力，持续12秒
    mod_sp2_repair_block = {
        "id": "skywarp_sp2_repair_block",
        "t": "heal_block",
        "tm": "",
        "tr": ["onSpecial2Hit"],
        "uit": ["onSpecial2Hit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "dmgFlags=LastHit",
        "trr": "repeat",
        "c": 1.0,
        "m": 1.0,
        "d": 12.0,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "heal_block_debuff",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_skywarp_sp2_repair_block"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_sp2_repair_block)
    mods[mod_sp2_repair_block["id"]] = mod_sp2_repair_block

    # =========================================================================
    # 7. 特殊技 3 (SP3): 能量窃取与能量涌动 (ID: 3328, 3329)
    # =========================================================================
    # 7.1 能量窃取: 对手扣除50%最大能量 (450 Mana) (ID: 3328)
    mod_sp3_drain = {
        "id": "skywarp_sp3_drain",
        "t": "power_gain",
        "tm": "",
        "tr": ["onSpecial3Hit"],
        "uit": ["onSpecial3Hit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "dmgFlags=LastHit",
        "trr": "repeat",
        "c": 1.0,
        "m": -450.0,
        "d": 0.5,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "power_drain",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_skywarp_sp3_power_steal"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_sp3_drain)
    mods[mod_sp3_drain["id"]] = mod_sp3_drain

    # 7.2 能量窃取: 我方获得50%最大能量 (450 Mana)
    mod_sp3_gain = {
        "id": "skywarp_sp3_gain",
        "t": "power_gain",
        "tm": "",
        "tr": ["onSpecial3Hit"],
        "uit": ["onSpecial3Hit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "dmgFlags=LastHit",
        "trr": "repeat",
        "c": 1.0,
        "m": 450.0,
        "d": 0.5,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "power_gain",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_skywarp_sp3_power_steal"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_sp3_gain)
    mods[mod_sp3_gain["id"]] = mod_sp3_gain

    # 7.3 永久能量涌动: 提升能量功率15% (ID: 3329)
    mod_sp3_power_flow = {
        "id": "skywarp_sp3_power_flow",
        "t": "power",
        "tm": "",
        "tr": ["onSpecial3Hit"],
        "uit": ["onSpecial3Hit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "dmgFlags=LastHit",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.15,
        "d": -1.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "power_flow_buff",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_skywarp_sp3_power_flow"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_sp3_power_flow)
    mods[mod_sp3_power_flow["id"]] = mod_sp3_power_flow

    return mods, appears, buffs
