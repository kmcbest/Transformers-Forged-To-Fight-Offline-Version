#!/usr/bin/env python3
"""
Bot Ability Implementation: 飞过山 (Cliffjumper)
================================================
Bot ID: cliffjumper_gs_kabam
阵营: 汽车人 (Autobot) | 职业: 勇士系 / 侦察兵 (Warrior / Scout)

【官方技能真理源对照 (来自 tools/new_bots_priority_specs.json 与 character_abilities)】：
-----------------------------------------------------------------------------
1. [ID: 3547 | 被动 - 玻璃瓦斯减益 / Glass Gas Debuff] (pua_icon: \uE524)
   - 官方描述: "远程攻击命中或被防，有100%的几率施加1层玻璃瓦斯减益，持续8秒可叠加。//灰色图标
                每层玻璃瓦斯减益降低对手格挡精通5% //格挡伤害相应放大5%
                每层玻璃瓦斯减益提升飞过山特殊技伤害5%"
   - 实现方案:
     cliffjumper_ranged_glass_gas: 远程命中或被防御时，100% 几率向对手施加 8 秒玻璃瓦斯减益，
     最多叠加 20 层。每层降低对手格挡精通 5%，提升特殊技伤害 5%。灰色图标 (E524)。

2. [ID: 3548 | 被动 - 重击刷新 / Heavy Refresh] (pua_icon: "")
   - 官方描述: "重击命中，刷新所有玻璃瓦斯减益的倒计时。"
   - 实现方案:
     cliffjumper_heavy_refresh_glass_gas: 重击命中时，刷新重置对手身上所有玻璃瓦斯减益的倒计时至 8 秒。

3. [ID: 3546 | 被动 - 特殊伤害 / Special Damage] (pua_icon: \uE41C)
   - 官方描述: "在没有伤害减益的状态下使用特殊技，伤害增加20%"
   - 实现方案:
     cliffjumper_clean_special_boost: 发动特殊技时如果自身未处于伤害减益状态，
     获得 20% 特殊伤害提升，持续 6 秒。暖橙色图标 (E41C)。

4. [ID: 3549 | 特殊技 1 - 玻璃瓦斯减益 / SP1 Glass Gas Debuff] (pua_icon: \uE524)
   - 官方描述: "施加1层永久玻璃瓦斯减益并刷新所有有倒计时的玻璃瓦斯减益  //永久减益和有倒计时的分两个图标"
   - 实现方案:
     a) cliffjumper_sp1_perm_glass_gas: SP1 命中施加 1 层永久玻璃瓦斯减益 (无倒计时)。
     b) cliffjumper_sp1_refresh_glass_gas: 刷新所有带倒计时的玻璃瓦斯减益。

5. [ID: 3541 | 特殊技 2 - 无法格挡 / SP2 Unblockable] (pua_icon: \uE41F)
   - 官方描述: "如果对手拥有至少I0个玻璃瓦斯减益，此攻击的最后一击无法格挡。"
   - 实现方案:
     cliffjumper_sp2_unblockable: SP2 最后一击命中前判定，若对手拥有 >=10 层玻璃瓦斯，
     获得无法格挡状态 (Unblockable)，强行破开敌方格挡。金黄色图标 (E41F)。

6. [ID: 3550 | 特殊技 3 - 玻璃瓦斯减益 / SP3 Glass Gas Debuff & Crit] (pua_icon: \uE524)
   - 官方描述: "施加5层永久玻璃瓦斯减益
                将所有带倒计时的玻璃瓦斯减益也变成永久减益
                最后一击的暴击几率增加60%"
   - 实现方案:
     a) cliffjumper_sp3_perm_glass_gas_5: SP3 施加 5 层永久玻璃瓦斯减益。
     b) cliffjumper_sp3_convert_perm_glass_gas: 将所有带倒计时的玻璃瓦斯转化为永久减益。
     c) cliffjumper_sp3_last_hit_crit_rate: SP3 最后一击获得 60% 暴击几率提升。
-----------------------------------------------------------------------------
"""

from ..core import (
    AbilityColor,
    make_crit_rate_statmod,
    make_statmod_appearance,
    validate_statmod,
    validate_appear,
)
from ..registry import register_bot

BOT_ID = "cliffjumper_gs_kabam"


@register_bot(BOT_ID, name_zh="飞过山", desc="玻璃瓦斯减益堆叠、重击刷新、SP1永久瓦斯、SP2瓦斯破防无法格挡与SP3极效粉碎")
def build_cliffjumper_abilities(base_hp: float = 34850.0, base_atk: float = 3485.0):
    """
    根据基准属性生成飞过山全部专属能力修饰器。
    基准 5星50级 HP = 34850.0, ATK = 3485.0
    """
    mods = {}
    appears = {}
    buffs = {
        # 飞过山倒计时玻璃瓦斯减益 (Glass Gas Debuff)
        "glass_gas": {
            "id": "glass_gas",
            "iconTexture": "",
            "image": "",
            "images3": False,
            "modeAvail": [],
            "scope": "global",
            "valueType": "multiplier",
            "displayValue": 0.05,
            "c": 1,
            "value": 0.05,
            "buffType": "debuff",
            "group": "glass_gas",
            "p": {"block_prof_reduction": 0.05, "special_dmg_boost": 0.05},
            "hasDuration": True,
            "e": 0,
            "time": {"amount": 8.0},
            "loc_name": "glass_gas",
            "loc_desc": "glass_gas",
        },
        # 飞过山永久玻璃瓦斯减益 (Permanent Glass Gas Debuff)
        "glass_gas_perm": {
            "id": "glass_gas_perm",
            "iconTexture": "",
            "image": "",
            "images3": False,
            "modeAvail": [],
            "scope": "global",
            "valueType": "multiplier",
            "displayValue": 0.05,
            "c": 1,
            "value": 0.05,
            "buffType": "debuff",
            "group": "glass_gas_perm",
            "p": {"block_prof_reduction": 0.05, "special_dmg_boost": 0.05},
            "hasDuration": False,
            "e": 0,
            "time": {"amount": 0.0},
            "loc_name": "glass_gas_perm",
            "loc_desc": "glass_gas_perm",
        },
    }

    # -------------------------------------------------------------------------
    # 1. [ID: 3547] 被动 - 玻璃瓦斯减益 (远程命中或被防 100% 施加 8s 玻璃瓦斯)
    # -------------------------------------------------------------------------
    appr_glass_gas = make_statmod_appearance(
        appr_id="appr_cliffjumper_glass_gas",
        callout_text="玻璃瓦斯",
        desc="降低对手格挡精通5%，并提升飞过山特殊技伤害5%，持续8秒",
        short_desc="玻璃瓦斯",
        pua_icon="\uE524",
        color=AbilityColor.GRAY_COOLDOWN,  # 官方灰色图标
        show_callout=True,
    )
    mod_ranged_glass_gas = {
        "id": "cliffjumper_ranged_glass_gas",
        "t": "glass_gas",
        "tm": "",
        "tr": ["onHit", "onBlock"],
        "uit": ["onHit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "level=Ranged",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.05,
        "d": 8.0,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 20,
        "g": "glass_gas",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_cliffjumper_glass_gas"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_appear(appr_glass_gas)
    validate_statmod(mod_ranged_glass_gas)
    appears[appr_glass_gas["id"]] = appr_glass_gas
    mods[mod_ranged_glass_gas["id"]] = mod_ranged_glass_gas

    # -------------------------------------------------------------------------
    # 2. [ID: 3548] 被动 - 重击刷新 (重击命中刷新所有玻璃瓦斯减益倒计时)
    # -------------------------------------------------------------------------
    mod_heavy_refresh = {
        "id": "cliffjumper_heavy_refresh_glass_gas",
        "t": "glass_gas",
        "tm": "cliffjumper_ranged_glass_gas",
        "tr": ["onHit"],
        "uit": [],
        "pri": 0,
        "trm": 0.0,
        "trs": "level=Heavy",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.05,
        "d": 8.0,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 20,
        "g": "glass_gas",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": [],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_heavy_refresh)
    mods[mod_heavy_refresh["id"]] = mod_heavy_refresh

    # -------------------------------------------------------------------------
    # 3. [ID: 3546] 被动 - 特殊伤害 (无伤害减益状态下使用特殊技，伤害增加20%)
    # -------------------------------------------------------------------------
    appr_clean_sp = make_statmod_appearance(
        appr_id="appr_cliffjumper_clean_sp",
        callout_text="特殊伤害",
        desc="无伤害减益状态下特殊技伤害提升20%",
        short_desc="特殊伤害",
        pua_icon="\uE41C",
        color=AbilityColor.ORANGE_DAMAGE,  # 橙色伤害增益
        show_callout=True,
    )
    mod_clean_sp = {
        "id": "cliffjumper_clean_special_boost",
        "t": "attack_buff",
        "tm": "",
        "tr": ["onSpecial1Activate", "onSpecial2Activate", "onSpecial3Activate"],
        "uit": ["onSpecial1Activate", "onSpecial2Activate", "onSpecial3Activate"],
        "pri": 0,
        "trm": 0.0,
        "trs": "self.status!=dmg_bleed,dmg_burn,dmg_shock,armor_break",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.20,
        "d": 6.0,
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
        "a": ["appr_cliffjumper_clean_sp"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_appear(appr_clean_sp)
    validate_statmod(mod_clean_sp)
    appears[appr_clean_sp["id"]] = appr_clean_sp
    mods[mod_clean_sp["id"]] = mod_clean_sp

    # -------------------------------------------------------------------------
    # 4. [ID: 3549] 特殊技 1 - 永久玻璃瓦斯减益与刷新
    # -------------------------------------------------------------------------
    appr_perm_glass_gas = make_statmod_appearance(
        appr_id="appr_cliffjumper_perm_glass_gas",
        callout_text="玻璃瓦斯",
        desc="永久降低对手格挡精通5%，并永久提升飞过山特殊技伤害5%",
        short_desc="永久瓦斯",
        pua_icon="\uE524",
        color=AbilityColor.GRAY_LOCKED,
        show_callout=True,
    )
    # (1) 施加 1 层永久玻璃瓦斯减益
    mod_sp1_perm = {
        "id": "cliffjumper_sp1_perm_glass_gas",
        "t": "glass_gas_perm",
        "tm": "",
        "tr": ["onSpecial1Hit"],
        "uit": ["onSpecial1Hit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.05,
        "d": -1.0,  # 永久常驻
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 20,
        "g": "glass_gas_perm",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_cliffjumper_perm_glass_gas"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_appear(appr_perm_glass_gas)
    validate_statmod(mod_sp1_perm)
    appears[appr_perm_glass_gas["id"]] = appr_perm_glass_gas
    mods[mod_sp1_perm["id"]] = mod_sp1_perm

    # (2) 刷新所有带倒计时的玻璃瓦斯
    mod_sp1_refresh = {
        "id": "cliffjumper_sp1_refresh_glass_gas",
        "t": "glass_gas",
        "tm": "cliffjumper_ranged_glass_gas",
        "tr": ["onSpecial1Hit"],
        "uit": [],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.05,
        "d": 8.0,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 20,
        "g": "glass_gas",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": [],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_sp1_refresh)
    mods[mod_sp1_refresh["id"]] = mod_sp1_refresh

    # -------------------------------------------------------------------------
    # 5. [ID: 3541] 特殊技 2 - 无法格挡 (对手拥有>=10层玻璃瓦斯时最后一击无法格挡)
    # -------------------------------------------------------------------------
    appr_sp2_unblockable = make_statmod_appearance(
        appr_id="appr_cliffjumper_sp2_unblockable",
        callout_text="不可防御",
        desc="对手瓦斯层数达到10层以上，最后一击无法格挡",
        short_desc="无法格挡",
        pua_icon="\uE41F",
        color=AbilityColor.YELLOW_STATUS,
        show_callout=True,
    )
    mod_sp2_unblockable = {
        "id": "cliffjumper_sp2_unblockable",
        "t": "unstoppable",  # 底层 unblockable / unstoppable 破防
        "tm": "",
        "tr": ["onSpecial2Hit", "onSpecial2Activate"],
        "uit": ["onSpecial2Hit"],
        "pri": 1,
        "trm": 0.0,
        "trs": "dmgFlags=LastHit;opp.status=glass_gas,glass_gas_perm>=10",
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
        "g": "unblockable",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_cliffjumper_sp2_unblockable"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_appear(appr_sp2_unblockable)
    validate_statmod(mod_sp2_unblockable)
    appears[appr_sp2_unblockable["id"]] = appr_sp2_unblockable
    mods[mod_sp2_unblockable["id"]] = mod_sp2_unblockable

    # -------------------------------------------------------------------------
    # 6. [ID: 3550] 特殊技 3 - 5层永久瓦斯、转化永久与最后一击暴击几率+60%
    # -------------------------------------------------------------------------
    # (1) 施加 5 层永久玻璃瓦斯减益
    mod_sp3_perm_5 = {
        "id": "cliffjumper_sp3_perm_glass_gas_5",
        "t": "glass_gas_perm",
        "tm": "",
        "tr": ["onSpecial3Hit"],
        "uit": ["onSpecial3Hit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.25,  # 5 层效果 (5 * 5% = 25%)
        "d": -1.0,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 20,
        "g": "glass_gas_perm",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_cliffjumper_perm_glass_gas"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_sp3_perm_5)
    mods[mod_sp3_perm_5["id"]] = mod_sp3_perm_5

    # (2) 将所有带倒计时的玻璃瓦斯转化为永久
    mod_sp3_convert = {
        "id": "cliffjumper_sp3_convert_perm_glass_gas",
        "t": "glass_gas_perm",
        "tm": "cliffjumper_ranged_glass_gas",
        "tr": ["onSpecial3Hit"],
        "uit": [],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.05,
        "d": -1.0,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 20,
        "g": "glass_gas_perm",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": [],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_sp3_convert)
    mods[mod_sp3_convert["id"]] = mod_sp3_convert

    # (3) 最后一击暴击几率增加 60%
    m_sp3_crit, a_sp3_crit = make_crit_rate_statmod(
        mod_id="cliffjumper_sp3_last_hit_crit_rate",
        duration=2.0,
        crit_bonus=0.60,
        chance=1.0,
        trigger="onSpecial3Hit",
        trigger_scope="dmgFlags=LastHit",
        appr_id="appr_cliffjumper_sp3_crit_rate",
        callout_text="暴击几率",
        pua_icon="\uE40D",
        color_hex="F59E0B",
        gradient_bottom="D97706",
    )
    mods.update(m_sp3_crit)
    appears.update(a_sp3_crit)

    return mods, appears, buffs
