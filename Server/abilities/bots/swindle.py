#!/usr/bin/env python3
"""
Bot Ability Implementation: 诈骗 (Swindle)
=============================================
Bot ID: swindle_gs
阵营: 霸天虎 (Decepticon) | 职业: 科技系 (Tech)

【官方技能真理源对照 (战车队军火掮客 · 科技系)】：
-----------------------------------------------------------------------------
1. [特殊技三重科技压制 / Tri-Effect Special Attacks]
   - 震击 / Shock (60% 几率造成 200% ATK 电磁伤害, 持续 6s)
   - 能量流失 / Power Leak (30% 几率扣除对手能量槽)
   - 眩晕 / Stun (10% 几率造成 3s 瘫痪眩晕)

2. [觉醒技 - 黑市护盾 / Black Market Shield] (pua_icon: 0xe515)
   - 描述: "当诈骗生命值跌破75%、50%或25%时，激活黑市应急科技护盾，100%减免即将受到的攻击伤害，持续8秒。"

3. [被动 - 军火改装系统 / Weapon Mod System] (pua_icon: 0xe306)
   - 描述: "重击启动4秒改装构建，完成后随机获得进攻/防御/能量改装中的一种（最多叠加3层）。"
   - 进攻改装: +30% 攻击力，提升特殊技震击几率 20%
   - 防御改装: +20% 减伤，提升特殊技眩晕几率 20%
   - 能量改装: +20% 能量功率，提升特殊技能量流失几率 20%

4. [被动 - 黑市暴利 / Black Market Windfall Heal] (pua_icon: 0xe503)
   - 描述: "若诈骗集齐三个同类型的改装模块，立即触发应急纳米自愈，恢复最大生命值的10%~20%。"

5. [特殊技 2 - 军火刷新 / SP2 Weapon Reroll]
   - 描述: "将已获得的所有改装模块随机替换重组。"

6. [特殊技 3 - 模块对齐 / SP3 Weapon Align]
   - 描述: "将所有改装模块调整为与第一个模块完全一致，触发黑市暴利回血。"
-----------------------------------------------------------------------------
"""

from ..core import (
    make_shock_statmod,
    make_power_leak_statmod,
    make_stun_statmod,
    make_armor_up_statmod,
    make_heal_statmod,
    make_attack_boost_statmod,
    validate_statmod,
    validate_appear,
    validate_color_code,
)
from ..registry import register_bot

BOT_ID = "swindle_gs"


@register_bot(BOT_ID, name_zh="诈骗", desc="霸天虎战车队军火专家·科技系，特殊技附带震击/能量流失/击晕三重高科技压制，黑市紧急护盾绝境免伤，三级军火改装与同频共振自愈")
def build_swindle_abilities(base_hp: float = 38520.0, base_atk: float = 2854.0):
    """
    根据基准属性生成诈骗全部专属能力修饰器。
    基准 5星50级 HP = 38520.0, ATK = 2854.0
    """
    mods = {}
    appears = {}
    buffs = {}

    # -------------------------------------------------------------------------
    # 1. SP1, SP2, SP3 三重科技压制
    # -------------------------------------------------------------------------
    sp_levels = [
        ("sp1", "onSpecial1Hit", "Special 1", "陀螺平衡破坏炮"),
        ("sp2", "onSpecial2Hit", "Special 2", "散射高爆离子弹"),
        ("sp3", "onSpecial3Hit", "Special 3", "战车突袭·军火狂潮"),
    ]

    for sp_key, sp_trigger, sp_label, sp_title in sp_levels:
        # 震击: 60% 基础几率 (由 Native Hook 统一根据进攻改装数量动态结算与精准施加)
        m_shock, a_shock = make_shock_statmod(
            mod_id=f"swindle_{sp_key}_shock",
            duration=6.0,
            total_dmg=float(round(base_atk * 2.0)),
            chance=1.0,
            trigger="none",
            trigger_scope="",
            appr_id=f"appr_swindle_{sp_key}_shock",
            callout_text="震击",
            pua_icon="\uE914",
            color_hex="FF0000",
            gradient_bottom="B91C1C",
        )
        m_shock[f"swindle_{sp_key}_shock"]["tr"] = []
        m_shock[f"swindle_{sp_key}_shock"]["uit"] = []
        mods.update(m_shock)
        appears.update(a_shock)

        # 能量流失: 30% 基础几率 (由 Native Hook 统一根据能量改装数量动态结算与精准施加)
        leak_drain = 1.0 if sp_key in ("sp2", "sp3") else 0.50
        m_leak, a_leak = make_power_leak_statmod(
            mod_id=f"swindle_{sp_key}_leak",
            duration=3.0,
            drain_bars=leak_drain,
            chance=1.0,
            trigger="none",
            trigger_scope="",
            appr_id=f"appr_swindle_{sp_key}_leak",
            callout_text="能量流失",
            pua_icon="\uE607",
            color_hex="FF0000",
            gradient_bottom="B91C1C",
        )
        m_leak[f"swindle_{sp_key}_leak"]["tr"] = []
        m_leak[f"swindle_{sp_key}_leak"]["uit"] = []
        mods.update(m_leak)
        appears.update(a_leak)

        # 眩晕: 10% 基础几率 (由 Native Hook 统一根据防御改装数量动态结算与精准施加)
        m_stun, a_stun = make_stun_statmod(
            mod_id=f"swindle_{sp_key}_stun",
            duration=3.0,
            chance=1.0,
            trigger="none",
            trigger_scope="",
            appr_id=f"appr_swindle_{sp_key}_stun",
            callout_text="眩晕",
            pua_icon="\uE605",
            color_hex="FFE000",
            gradient_bottom="FFAA00",
        )
        m_stun[f"swindle_{sp_key}_stun"]["tr"] = []
        m_stun[f"swindle_{sp_key}_stun"]["uit"] = []
        mods.update(m_stun)
        appears.update(a_stun)

    # -------------------------------------------------------------------------
    # 2. 觉醒技 - 黑市护盾: 血量跌破 75%/50%/25% 触发 8s 100% 减伤护盾
    # -------------------------------------------------------------------------
    validate_color_code("29EBF4", "swindle_force_shield_tc")
    validate_color_code("00C5E8", "swindle_force_shield_gb")
    appr_force_shield = {
        "id": "appr_swindle_force_shield",
        "a": "黑市护盾",
        "s": "",
        "l": "黑市应急护盾生效中，100%减免即将受到的伤害8秒",
        "ss": "黑市护盾",
        "t": "\uE515",
        "f": "",
        "st": "增益",
        "ps": "护盾",
        "pl": "护盾效果",
        "tc": "29EBF4",
        "gt": "29EBF4",
        "gb": "00C5E8",
    }
    validate_appear(appr_force_shield)
    appears["appr_swindle_force_shield"] = appr_force_shield

    mod_force_shield = {
        "id": "swindle_sig_force_shield",
        "t": "force_shield",
        "tm": "",
        "tr": [],
        "uit": [],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
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
        "g": "force_shield",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_swindle_force_shield"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_force_shield)
    mods["swindle_sig_force_shield"] = mod_force_shield

    # -------------------------------------------------------------------------
    # 2.1 被动改装系统 - 重击构建 (4.0s 灰色倒计时图标)
    # -------------------------------------------------------------------------
    validate_color_code("CBD5E1", "swindle_build_tc")
    validate_color_code("94A3B8", "swindle_build_gb")
    appr_building = {
        "id": "appr_swindle_upgrade_building",
        "a": "改装中",
        "s": "",
        "l": "诈骗正在构建军火改装模块，持续4秒，若被暴击则构建失败",
        "ss": "改装中",
        "t": "\uE306",
        "f": "",
        "st": "构建",
        "ps": "构建",
        "pl": "构建中",
        "tc": "CBD5E1",
        "gt": "CBD5E1",
        "gb": "94A3B8",
    }
    validate_appear(appr_building)
    appears["appr_swindle_upgrade_building"] = appr_building

    mod_building = {
        "id": "swindle_upgrade_building",
        "t": "cooldown",
        "tm": "",
        "tr": [],
        "uit": [],
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
        "g": "swindle_building",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_swindle_upgrade_building"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_building)
    mods["swindle_upgrade_building"] = mod_building

    # -------------------------------------------------------------------------
    # 2.2 进攻改装 (+30% 攻击力，特殊技震击几率+20%) - 橙色图标
    # -------------------------------------------------------------------------
    m_up_atk, a_up_atk = make_attack_boost_statmod(
        mod_id="swindle_upgrade_attack",
        duration=-1.0,
        attack_bonus=0.30,
        chance=1.0,
        trigger="none",
        trigger_scope="",
        appr_id="appr_swindle_upgrade_attack",
        callout_text="进攻改装",
        pua_icon="\uE306",
        color_hex="FF8800",
        gradient_bottom="DD6600",
        stackable=True,
        max_stacks=3,
    )
    m_up_atk["swindle_upgrade_attack"]["tr"] = []
    m_up_atk["swindle_upgrade_attack"]["uit"] = []
    mods.update(m_up_atk)
    appears.update(a_up_atk)

    # -------------------------------------------------------------------------
    # 2.3 防御改装 (+20% 减伤，特殊技眩晕几率+20%) - 蓝色图标
    # -------------------------------------------------------------------------
    m_up_def, a_up_def = make_armor_up_statmod(
        mod_id="swindle_upgrade_defense",
        duration=-1.0,
        armor_bonus=0.20,
        chance=1.0,
        trigger="none",
        trigger_scope="",
        appr_id="appr_swindle_upgrade_defense",
        callout_text="防御改装",
        pua_icon="\uE306",
        color_hex="29EBF4",
        gradient_bottom="00C5E8",
        stackable=True,
        max_stacks=3,
    )
    m_up_def["swindle_upgrade_defense"]["tr"] = []
    m_up_def["swindle_upgrade_defense"]["uit"] = []
    mods.update(m_up_def)
    appears.update(a_up_def)

    # -------------------------------------------------------------------------
    # 2.4 能量改装 (+20% 能量功率，特殊技能量流失几率+20%) - 紫色图标
    # -------------------------------------------------------------------------
    validate_color_code("C4BBF8", "swindle_power_tc")
    validate_color_code("7E22CE", "swindle_power_gb")
    appr_power = {
        "id": "appr_swindle_upgrade_power",
        "a": "能量改装",
        "s": "",
        "l": "提升20%能量功率与能量流失几率",
        "ss": "能量改装",
        "t": "\uE306",
        "f": "",
        "st": "能量改装",
        "ps": "能量改装",
        "pl": "能量改装生效中",
        "tc": "C4BBF8",
        "gt": "C4BBF8",
        "gb": "7E22CE",
    }
    validate_appear(appr_power)
    appears["appr_swindle_upgrade_power"] = appr_power

    mod_power = {
        "id": "swindle_upgrade_power",
        "t": "power_rate",
        "tm": "",
        "tr": [],
        "uit": [],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.20,
        "d": -1.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 3,
        "g": "swindle_upgrade",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_swindle_upgrade_power"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_power)
    mods["swindle_upgrade_power"] = mod_power

    # -------------------------------------------------------------------------
    # 3. 被动 - 改装成功自愈: 三个同类改装触发立即修复 10%~20% HP
    # -------------------------------------------------------------------------
    m_succ_heal, a_succ_heal = make_heal_statmod(
        mod_id="swindle_upgrade_success_heal",
        duration=0.0,
        heal_amount=0.0,
        chance=1.0,
        trigger="none",
        trigger_scope="",
        appr_id="appr_swindle_success_heal",
        callout_text="黑市暴利",
        pua_icon="\uE503",
        color_hex="10B981",
        gradient_bottom="059669",
    )
    m_succ_heal["swindle_upgrade_success_heal"]["tr"] = []
    m_succ_heal["swindle_upgrade_success_heal"]["uit"] = []
    mods.update(m_succ_heal)
    appears.update(a_succ_heal)

    # -------------------------------------------------------------------------
    # 4. 特殊技 2 - 军火刷新: 随机重置已有改装类型
    # -------------------------------------------------------------------------
    validate_color_code("38BDF8", "swindle_reroll_tc")
    validate_color_code("0284C7", "swindle_reroll_gb")
    appr_reroll = {
        "id": "appr_swindle_sp2_reroll",
        "a": "军火刷新",
        "s": "",
        "l": "随机替换所有已获得的军火改装类型",
        "ss": "军火刷新",
        "t": "\uE306",
        "f": "",
        "st": "军火刷新",
        "ps": "军火刷新",
        "pl": "军火刷新生效中",
        "tc": "38BDF8",
        "gt": "38BDF8",
        "gb": "0284C7",
    }
    validate_appear(appr_reroll)
    appears["appr_swindle_sp2_reroll"] = appr_reroll

    mod_reroll = {
        "id": "swindle_sp2_reroll_upgrades",
        "t": "reroll_buffs",
        "tm": "",
        "tr": ["onSpecial2Hit"],
        "uit": ["onSpecial2Hit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "dmgFlags=LastHit",
        "trr": "repeat",
        "c": 1.0,
        "m": 1.0,
        "d": 0.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "swindle_upgrade",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_swindle_sp2_reroll"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_reroll)
    mods["swindle_sp2_reroll_upgrades"] = mod_reroll

    # -------------------------------------------------------------------------
    # 5. 特殊技 3 - 模块对齐: 使所有改装类型与首个模块保持一致
    # -------------------------------------------------------------------------
    validate_color_code("38BDF8", "swindle_align_tc")
    validate_color_code("0284C7", "swindle_align_gb")
    appr_align = {
        "id": "appr_swindle_sp3_align",
        "a": "模块对齐",
        "s": "",
        "l": "将所有改装转变为首个模块相同类型并触发黑市暴利回血",
        "ss": "模块对齐",
        "t": "\uE306",
        "f": "",
        "st": "模块对齐",
        "ps": "模块对齐",
        "pl": "模块对齐生效中",
        "tc": "38BDF8",
        "gt": "38BDF8",
        "gb": "0284C7",
    }
    validate_appear(appr_align)
    appears["appr_swindle_sp3_align"] = appr_align

    mod_align = {
        "id": "swindle_sp3_align_upgrades",
        "t": "normalize_buffs",
        "tm": "",
        "tr": ["onSpecial3Hit"],
        "uit": ["onSpecial3Hit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "dmgFlags=LastHit",
        "trr": "repeat",
        "c": 1.0,
        "m": 1.0,
        "d": 0.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "swindle_upgrade",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_swindle_sp3_align"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_align)
    mods["swindle_sp3_align_upgrades"] = mod_align

    return mods, appears, buffs
