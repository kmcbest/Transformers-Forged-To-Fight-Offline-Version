#!/usr/bin/env python3
"""
Bot Ability Implementation: 震荡波 (Shockwave)
==============================================
Bot ID: shockwave_gs
阵营: 霸天虎 (Decepticon) | 职业: 科技系 (Tech)

【官方技能真理源对照 (来自 tools/new_bots_priority_specs.json)】：
-----------------------------------------------------------------------------
1. [被动 - 能量充能 / Energy Charge] (ID: 3277, category: passive)
   - 官方描述: "格挡远程能量攻击时，得到1层能量充能，持续6秒，最多叠加3层  //大部分远程普通攻击都是能量攻击，只有漂移、反冲和雷震是物理攻击，他们不会给震荡波得到护盾。
震荡波能量充能数少于3个时，格挡远程能量攻击承受0伤害。"

2. [觉醒技 - 回溯 / Undo] (ID: 3283, pua_icon: 0xe81e, category: signature)
   - 官方描述: "每充满一格能量时，有35%的概率激活回溯，持续4秒。当倒计时结束时，他会立即修复这4秒内受到的全部伤害。//灰色图标"

3. [特殊技 2 - 护甲穿透 / Armor Piercing] (ID: 3285, pua_icon: 0xe409, category: sp2)
   - 官方描述: "技能期间100%护甲穿透   //黄图标，技能期间显示"

4. [特殊技 1 - 能量充能 / SP1 Energy Charge] (ID: 3301, category: sp1)
   - 官方描述: "技能发动时（无论是否命中），得到3层能量充能，持续6秒"

5. [特殊技 1 - 震击 / SP1 Shock] (ID: 3302, pua_icon: 0xe914, category: sp1)
   - 官方描述: "最后一击命中时，每层能量充能施加1层震击减益，造成攻击力85%的伤害，持续4秒"

6. [特殊技 2 - 阻止修复 / SP2 Repair Block] (ID: 3303, pua_icon: 0xe90c, category: sp2)
   - 官方描述: "最后一击命中，施加阻止修复，禁用对方所有回血能力，持续6.5秒"

7. [被动/SP2 - 能量充能 / SP2 Energy Charge] (ID: 3304, category: passive)
   - 官方描述: "技能发动时（无论是否命中），得到3层能量充能，持续6秒"

8. [被动 - 震击与能量流失 / Shock & Power Leak] (ID: 3300, pua_icon: 0xe914, category: passive)
   - 官方描述: "重击命中时，每层能量充能施加1层震击减益，造成攻击力85%的伤害，持续4秒  // 不消耗能量充能，无能量充能则不触发震击
普通远程攻击命中时，如果有能量充能，消耗1层能量充能，施加1层震击减益，造成攻击力85%的伤害，持续4秒  // 无能量充能则不触发震击
震击的同时触发能量流失，每秒扣除最大能量的0.87%，直到震击结束或者被净化  // 同步显示红色能量流失图标e607"

9. [特殊技 3 - 能量充能 / SP3 Energy Charge] (ID: 3307, category: sp3)
   - 官方描述: "技能发动时，得到5层能量充能，持续7秒"

10. [特殊技 3 - 震击 / SP3 Shock] (ID: 3308, pua_icon: 0xe914, category: sp3)
    - 官方描述: "技能完成后，每层能量充能施加1层震击减益，造成攻击力85%的伤害，持续4秒"

11. [特殊技 3 - 阻止修复 / SP3 Repair Block] (ID: 3309, pua_icon: 0xe90c, category: sp3)
    - 官方描述: "技能完成后，施加阻止修复，禁用对方所有回血能力，持续11秒"
-----------------------------------------------------------------------------
"""

from ..core import (
    AbilityColor,
    make_shock_statmod,
    make_power_leak_statmod,
    make_statmod_appearance,
    validate_statmod,
    validate_appear,
    validate_color_code,
)
from ..registry import register_bot

BOT_ID = "shockwave_gs"


@register_bot(BOT_ID, name_zh="震荡波", desc="科技系冷酷逻辑官，能量充能循环转化、强力触电震击与能量流失、回溯逆转伤害、SP2护甲穿透与强效禁疗阻止修复")
def build_shockwave_abilities(base_hp: float = 34850.0, base_atk: float = 3485.0):
    """
    根据基准属性生成震荡波全部专属能力修饰器。
    基准 5星50级 HP = 34850.0, ATK = 3485.0
    """
    mods = {}
    appears = {}
    buffs = {
        # 震荡波震击持续能量伤害 (Shock DOT)
        "dmg_shock": {
            "id": "dmg_shock",
            "iconTexture": "",
            "image": "",
            "images3": False,
            "modeAvail": [],
            "scope": "global",
            "valueType": "absolute",
            "displayValue": float(round(base_atk * 0.85)),
            "c": 1,
            "value": float(round(base_atk * 0.85)),
            "buffType": "damage",
            "group": "dmg_shock",
            "p": {"damage_type": "shock"},
            "hasDuration": True,
            "e": 0,
            "time": {"amount": 4.0},
            "loc_name": "shock",
            "loc_desc": "shock",
        },
    }

    # =========================================================================
    # 1. 通用外观 (StatModAppearances)
    # =========================================================================
    # 1.1 能量充能外观 (浅紫色能量图标)
    appr_energy_charge = make_statmod_appearance(
        appr_id="appr_shockwave_energy_charge",
        callout_text="能量充能",
        desc="格挡远程能量攻击或激活特殊技获得能量充能，提升防御并为震击充能",
        pua_icon="\uE914",
        color=AbilityColor.LIGHT_PURPLE_POWER,
        show_callout=True,
    )
    validate_appear(appr_energy_charge)
    appears[appr_energy_charge["id"]] = appr_energy_charge

    # 1.2 觉醒技 - 回溯外观 (灰色图标)
    appr_undo = make_statmod_appearance(
        appr_id="appr_shockwave_undo",
        callout_text="回溯",
        desc="充满能量时激活回溯，倒计时结束时修复期间受到的伤害",
        pua_icon="\uE81E",
        color=AbilityColor.GRAY_COOLDOWN,
        show_callout=True,
    )
    validate_appear(appr_undo)
    appears[appr_undo["id"]] = appr_undo

    # 1.3 SP2 护甲穿透外观 (黄色图标)
    appr_sp2_pierce = make_statmod_appearance(
        appr_id="appr_shockwave_sp2_pierce",
        callout_text="护甲穿透",
        desc="技能期间获得100%护甲穿透",
        pua_icon="\uE409",
        color=AbilityColor.YELLOW_STATUS,
        show_callout=True,
    )
    validate_appear(appr_sp2_pierce)
    appears[appr_sp2_pierce["id"]] = appr_sp2_pierce

    # 1.4 SP2 阻止修复外观 (红色Debuff图标)
    appr_sp2_repair_block = make_statmod_appearance(
        appr_id="appr_shockwave_sp2_repair_block",
        callout_text="阻止修复",
        desc="禁用对方所有生命回复能力持续6.5秒",
        pua_icon="\uE90C",
        color=AbilityColor.RED_DEBUFF,
        show_callout=True,
    )
    validate_appear(appr_sp2_repair_block)
    appears[appr_sp2_repair_block["id"]] = appr_sp2_repair_block

    # 1.5 SP3 阻止修复外观 (红色Debuff图标)
    appr_sp3_repair_block = make_statmod_appearance(
        appr_id="appr_shockwave_sp3_repair_block",
        callout_text="阻止修复",
        desc="技能完成后禁用对方所有生命回复能力持续11秒",
        pua_icon="\uE90C",
        color=AbilityColor.RED_DEBUFF,
        show_callout=True,
    )
    validate_appear(appr_sp3_repair_block)
    appears[appr_sp3_repair_block["id"]] = appr_sp3_repair_block

    # =========================================================================
    # 2. 被动能力：格挡能量充能与伤害吸收 (ID: 3277)
    # =========================================================================
    # 格挡远程能量攻击获得1层能量充能，持续6秒，最多3层
    mod_block_charge = {
        "id": "shockwave_block_energy_charge",
        "t": "power",
        "tm": "",
        "tr": ["onPlayerStateEnter"],
        "uit": ["onPlayerStateEnter"],
        "pri": 0,
        "trm": 0.0,
        "trs": "state=Block",
        "trr": "repeat",
        "c": 1.0,
        "m": 1.0,
        "d": 6.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 3,
        "g": "energy_charge",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_shockwave_energy_charge"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_block_charge)
    mods[mod_block_charge["id"]] = mod_block_charge

    # 充能少于3个时格挡承受0伤害 (高额护甲格挡防御加成)
    mod_block_absorb = {
        "id": "shockwave_block_absorb",
        "t": "armor",
        "tm": "",
        "tr": ["onPlayerStateEnter"],
        "uit": ["onPlayerStateEnter"],
        "pri": 0,
        "trm": 0.0,
        "trs": "state=Block",
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
        "g": "block_armor",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_shockwave_energy_charge"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_block_absorb)
    mods[mod_block_absorb["id"]] = mod_block_absorb

    # =========================================================================
    # 3. 觉醒技：回溯 (ID: 3283)
    # =========================================================================
    # 每充满一格能量时，35%概率激活回溯，持续4秒，结束时修复4秒内受到的伤害
    mod_sig_undo = {
        "id": "shockwave_sig_undo",
        "t": "heal",
        "tm": "",
        "tr": ["onHit"],
        "uit": ["onHit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 0.35,
        "m": float(round(base_hp * 0.15, 2)),
        "d": 4.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "undo_buff",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_shockwave_undo"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_sig_undo)
    mods[mod_sig_undo["id"]] = mod_sig_undo

    # =========================================================================
    # 4. 被动：重击/远程震击与能量流失 (ID: 3300)
    # =========================================================================
    # 4.1 重击震击: 85% ATK, 4.0s
    m_heavy_shock, a_heavy_shock = make_shock_statmod(
        mod_id="shockwave_heavy_shock",
        duration=4.0,
        total_dmg=float(round(base_atk * 0.85)),
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Heavy",
        appr_id="appr_shockwave_shock",
        callout_text="震击",
        pua_icon="\uE914",
    )
    mods.update(m_heavy_shock)
    appears.update(a_heavy_shock)

    # 4.2 普通远程震击: 85% ATK, 4.0s
    m_ranged_shock, a_ranged_shock = make_shock_statmod(
        mod_id="shockwave_ranged_shock",
        duration=4.0,
        total_dmg=float(round(base_atk * 0.85)),
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Ranged",
        appr_id="appr_shockwave_shock",
        callout_text="震击",
        pua_icon="\uE914",
    )
    mods.update(m_ranged_shock)
    appears.update(a_ranged_shock)

    # 4.3 震击同时触发能量流失: 每秒0.87%，4秒扣除3.48%最大能量 (0.1044格)
    m_shk_leak, a_shk_leak = make_power_leak_statmod(
        mod_id="shockwave_shock_power_leak",
        duration=4.0,
        drain_bars=0.1044,
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Heavy,Ranged",
        appr_id="appr_shockwave_power_leak",
        callout_text="能量流失",
        pua_icon="\uE607",
    )
    mods.update(m_shk_leak)
    appears.update(a_shk_leak)

    # =========================================================================
    # 5. 特殊技 1 (SP1): 充能与震击 (ID: 3301, 3302)
    # =========================================================================
    # 5.1 SP1 发动时获得3层能量充能，持续6秒 (ID: 3301)
    mod_sp1_charge = {
        "id": "shockwave_sp1_charge",
        "t": "power",
        "tm": "",
        "tr": ["onSpecial1Activate"],
        "uit": ["onSpecial1Activate"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 3.0,
        "d": 6.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 10,
        "g": "energy_charge",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_shockwave_energy_charge"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_sp1_charge)
    mods[mod_sp1_charge["id"]] = mod_sp1_charge

    # 5.2 SP1 最后一击施加震击: 85% ATK, 4.0s (ID: 3302)
    m_sp1_shock, a_sp1_shock = make_shock_statmod(
        mod_id="shockwave_sp1_shock",
        duration=4.0,
        total_dmg=float(round(base_atk * 0.85)),
        chance=1.0,
        trigger="onSpecial1Hit",
        trigger_scope="dmgFlags=LastHit",
        appr_id="appr_shockwave_shock",
        callout_text="震击",
        pua_icon="\uE914",
    )
    mods.update(m_sp1_shock)
    appears.update(a_sp1_shock)

    # =========================================================================
    # 6. 特殊技 2 (SP2): 护甲穿透、充能与阻止修复 (ID: 3285, 3304, 3303)
    # =========================================================================
    # 6.1 SP2 技能期间100%护甲穿透 (ID: 3285)
    mod_sp2_pierce = {
        "id": "shockwave_sp2_pierce",
        "t": "armor_pierce",
        "tm": "",
        "tr": ["onSpecial2Activate"],
        "uit": ["onSpecial2Activate"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 1.0,
        "d": 3.5,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "armor_pierce",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_shockwave_sp2_pierce"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_sp2_pierce)
    mods[mod_sp2_pierce["id"]] = mod_sp2_pierce

    # 6.2 SP2 发动时获得3层能量充能，持续6秒 (ID: 3304)
    mod_sp2_charge = {
        "id": "shockwave_sp2_charge",
        "t": "power",
        "tm": "",
        "tr": ["onSpecial2Activate"],
        "uit": ["onSpecial2Activate"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 3.0,
        "d": 6.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 10,
        "g": "energy_charge",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_shockwave_energy_charge"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_sp2_charge)
    mods[mod_sp2_charge["id"]] = mod_sp2_charge

    # 6.3 SP2 最后一击施加阻止修复，持续6.5秒 (ID: 3303)
    mod_sp2_repair_block = {
        "id": "shockwave_sp2_repair_block",
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
        "d": 6.5,
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
        "a": ["appr_shockwave_sp2_repair_block"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_sp2_repair_block)
    mods[mod_sp2_repair_block["id"]] = mod_sp2_repair_block

    # =========================================================================
    # 7. 特殊技 3 (SP3): 充能、震击与阻止修复 (ID: 3307, 3308, 3309)
    # =========================================================================
    # 7.1 SP3 发动时获得5层能量充能，持续7秒 (ID: 3307)
    mod_sp3_charge = {
        "id": "shockwave_sp3_charge",
        "t": "power",
        "tm": "",
        "tr": ["onSpecial3Activate"],
        "uit": ["onSpecial3Activate"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 5.0,
        "d": 7.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 10,
        "g": "energy_charge",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_shockwave_energy_charge"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_sp3_charge)
    mods[mod_sp3_charge["id"]] = mod_sp3_charge

    # 7.2 SP3 完成后施加震击: 85% ATK, 4.0s (ID: 3308)
    m_sp3_shock, a_sp3_shock = make_shock_statmod(
        mod_id="shockwave_sp3_shock",
        duration=4.0,
        total_dmg=float(round(base_atk * 0.85)),
        chance=1.0,
        trigger="onSpecial3Hit",
        trigger_scope="dmgFlags=LastHit",
        appr_id="appr_shockwave_shock",
        callout_text="震击",
        pua_icon="\uE914",
    )
    mods.update(m_sp3_shock)
    appears.update(a_sp3_shock)

    # 7.3 SP3 完成后施加阻止修复，持续11秒 (ID: 3309)
    mod_sp3_repair_block = {
        "id": "shockwave_sp3_repair_block",
        "t": "heal_block",
        "tm": "",
        "tr": ["onSpecial3Hit"],
        "uit": ["onSpecial3Hit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "dmgFlags=LastHit",
        "trr": "repeat",
        "c": 1.0,
        "m": 1.0,
        "d": 11.0,
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
        "a": ["appr_shockwave_sp3_repair_block"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_sp3_repair_block)
    mods[mod_sp3_repair_block["id"]] = mod_sp3_repair_block

    return mods, appears, buffs
