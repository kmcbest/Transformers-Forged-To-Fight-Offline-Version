#!/usr/bin/env python3
"""
Bot Ability Implementation: 千斤顶 (Wheeljack)
=============================================
Bot ID: wheeljack_gs_mp20
阵营: 汽车人 (Autobot) | 职业: 科技系 (Tech)

【官方技能真理源对照 (来自在线优先实现)】：
-----------------------------------------------------------------------------
1. [特殊技三合一打击 / Tri-Effect Special Attacks]
   - 震击 / Shock (60% 几率 200% ATK, 6s)
   - 能量流失 / Power Leak (扣除能量)
   - 眩晕 / Stun (10% 几率 3s 眩晕)

2. [觉醒技 - 力量护盾 / Force Shield] (ID: 2888, pua_icon: 0xe515)
   - 描述: "如果敌人的攻击将千斤顶的生命值降低到75%，50%或25%以下，力量护盾将激活，100%降低敌人攻击造成的所有伤害，持续8秒。"

3. [被动 - 成功 / Upgrade Success Heal] (ID: 3658, pua_icon: 0xe503)
   - 描述: "如果千斤顶得到三个同样的升级，会触发立即回血，恢复最大生命值的15%。"

4. [特殊技 2 - 刷新升级 / SP2 Reroll Upgrades] (ID: 3659)
   - 描述: "把已有的升级全部随机替换（攻击/防御/能量三选一）。"

5. [特殊技 3 - 升级对齐 / SP3 Align Upgrades] (ID: 3660)
   - 描述: "把所有升级变成与第一个升级相同，凑齐三同升级触发回血。"
-----------------------------------------------------------------------------
"""

from ..core import (
    make_shock_statmod,
    make_power_leak_statmod,
    make_stun_statmod,
    make_armor_up_statmod,
    make_heal_statmod,
    validate_statmod,
    validate_appear,
    validate_color_code,
)
from ..registry import register_bot

BOT_ID = "wheeljack_gs_mp20"


@register_bot(BOT_ID, name_zh="千斤顶", desc="科技系发明家，特殊技附带震击/能量流失/击晕三重科技打击，紧急力量护盾绝境免伤，三级科技模块升级与同频共振自愈")
def build_wheeljack_abilities(base_hp: float = 32402.0, base_atk: float = 2306.0):
    """
    根据基准属性生成千斤顶全部专属能力修饰器。
    基准 5星50级 HP = 32402.0, ATK = 2306.0
    """
    mods = {}
    appears = {}
    buffs = {}

    # -------------------------------------------------------------------------
    # 1. SP1, SP2, SP3 三合一科技打击
    # -------------------------------------------------------------------------
    sp_levels = [
        ("sp1", "onSpecial1Hit", "Special 1", "原型"),
        ("sp2", "onSpecial2Hit", "Special 2", "迭代"),
        ("sp3", "onSpecial3Hit", "Special 3", "完美"),
    ]

    for sp_key, sp_trigger, sp_label, sp_title in sp_levels:
        # 震击: 60% 几率 200% ATK 6s
        m_shock, a_shock = make_shock_statmod(
            mod_id=f"wheeljack_{sp_key}_shock",
            duration=6.0,
            total_dmg=float(round(base_atk * 2.0)),
            chance=0.60,
            trigger=sp_trigger,
            trigger_scope="dmgFlags=LastHit",
            appr_id=f"appr_wheeljack_{sp_key}_shock",
            callout_text="震击",
            pua_icon="\uE914",
            color_hex="FF0000",
            gradient_bottom="B91C1C",
        )
        mods.update(m_shock)
        appears.update(a_shock)

        # 能量流失
        leak_chance = 1.0 if sp_key in ("sp2", "sp3") else 0.50
        leak_drain = 1.0 if sp_key in ("sp2", "sp3") else 0.50
        m_leak, a_leak = make_power_leak_statmod(
            mod_id=f"wheeljack_{sp_key}_leak",
            duration=3.0,
            drain_bars=leak_drain,
            chance=leak_chance,
            trigger=sp_trigger,
            trigger_scope="dmgFlags=LastHit",
            appr_id=f"appr_wheeljack_{sp_key}_leak",
            callout_text="能量流失",
            pua_icon="\uE607",
            color_hex="FF0000",
            gradient_bottom="B91C1C",
        )
        mods.update(m_leak)
        appears.update(a_leak)

        # 眩晕
        m_stun, a_stun = make_stun_statmod(
            mod_id=f"wheeljack_{sp_key}_stun",
            duration=3.0,
            chance=0.10,
            trigger=sp_trigger,
            trigger_scope="dmgFlags=LastHit",
            appr_id=f"appr_wheeljack_{sp_key}_stun",
            callout_text="眩晕",
            pua_icon="\uE605",
            color_hex="FFE000",
            gradient_bottom="FFAA00",
        )
        mods.update(m_stun)
        appears.update(a_stun)

    # -------------------------------------------------------------------------
    # 2. 觉醒技 - 力量护盾 (ID: 2888): 血量跌破 75%/50%/25% 触发 8s 100% 减伤护盾
    # -------------------------------------------------------------------------
    m_force_shield, a_force_shield = make_armor_up_statmod(
        mod_id="wheeljack_sig_force_shield",
        duration=8.0,
        armor_bonus=1.00,
        chance=1.0,
        trigger="onPlayerStateEnter",
        trigger_scope="threshold=0.75,0.50,0.25",
        appr_id="appr_wheeljack_force_shield",
        callout_text="力量护盾",
        pua_icon="\uE515",
        color_hex="29EBF4",
        gradient_bottom="00C5E8",
    )
    mods.update(m_force_shield)
    appears.update(a_force_shield)

    # -------------------------------------------------------------------------
    # 3. 被动 - 升级成功自愈 (ID: 3658): 三个同类升级触发立即修复 15% HP
    # -------------------------------------------------------------------------
    m_succ_heal, a_succ_heal = make_heal_statmod(
        mod_id="wheeljack_upgrade_success_heal",
        duration=0.0,
        heal_amount=float(round(base_hp * 0.15)),
        chance=1.0,
        trigger="always",
        trigger_scope="upgrades_match=3",
        appr_id="appr_wheeljack_success_heal",
        callout_text="升级成功",
        pua_icon="\uE503",
        color_hex="10B981",
        gradient_bottom="059669",
    )
    mods.update(m_succ_heal)
    appears.update(a_succ_heal)

    # -------------------------------------------------------------------------
    # 4. 特殊技 2 - 刷新升级 (ID: 3659): 随机重置已有升级类型
    # -------------------------------------------------------------------------
    validate_color_code("38BDF8", "reroll_tc")
    validate_color_code("0284C7", "reroll_gb")
    appr_reroll = {
        "id": "appr_wheeljack_sp2_reroll",
        "a": "升级刷新",
        "s": "升级刷新",
        "l": "随机替换所有已获得的科技升级类型",
        "ss": "升级刷新",
        "t": "\uE950",
        "f": "",
        "st": "升级刷新",
        "ps": "升级刷新",
        "pl": "升级刷新生效中",
        "tc": "38BDF8",
        "gt": "38BDF8",
        "gb": "0284C7",
    }
    validate_appear(appr_reroll)
    appears["appr_wheeljack_sp2_reroll"] = appr_reroll

    mod_reroll = {
        "id": "wheeljack_sp2_reroll_upgrades",
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
        "g": "wheeljack_upgrade",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_wheeljack_sp2_reroll"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_reroll)
    mods["wheeljack_sp2_reroll_upgrades"] = mod_reroll

    # -------------------------------------------------------------------------
    # 5. 特殊技 3 - 升级对齐 (ID: 3660): 使所有升级类型与首个升级保持一致
    # -------------------------------------------------------------------------
    validate_color_code("38BDF8", "align_tc")
    validate_color_code("0284C7", "align_gb")
    appr_align = {
        "id": "appr_wheeljack_sp3_align",
        "a": "升级对齐",
        "s": "升级对齐",
        "l": "将所有升级转变为首个升级相同类型并触发升级成功",
        "ss": "升级对齐",
        "t": "\uE950",
        "f": "",
        "st": "升级对齐",
        "ps": "升级对齐",
        "pl": "升级对齐生效中",
        "tc": "38BDF8",
        "gt": "38BDF8",
        "gb": "0284C7",
    }
    validate_appear(appr_align)
    appears["appr_wheeljack_sp3_align"] = appr_align

    mod_align = {
        "id": "wheeljack_sp3_align_upgrades",
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
        "g": "wheeljack_upgrade",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_wheeljack_sp3_align"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_align)
    mods["wheeljack_sp3_align_upgrades"] = mod_align

    return mods, appears, buffs
