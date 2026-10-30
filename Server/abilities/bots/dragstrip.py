#!/usr/bin/env python3
"""
Bot Ability Implementation: 抢劫 (Dragstrip)
============================================
Bot ID: dragstrip_gs_deluxe2016
阵营: 霸天虎 (Decepticon) | 职业: 侦察兵 (Scout)

【官方技能真理源对照 (来自 tools/new_bots_priority_specs.json 与 character_abilities)】：
-----------------------------------------------------------------------------
1. [ID: 3516 | 觉醒技 - 卑鄙胜者 / Dirty Victory] (pua_icon: \uE607)
   - 官方描述: "重击命中有45%概率窃取对方最大能量的10%，并施加1层流血，造成攻击力40%的伤害，持续5秒。"
   - 实现方案:
     a) dragstrip_sig_power_steal: 重击命中 45% 概率吸取对手 10% 最大能量 (30 点 Mana)。
     b) dragstrip_sig_bleed: 重击命中 45% 概率施加 5 秒流血 (40% ATK 物理伤害)。

2. [ID: 3524 | 被动 - 不可防御 / Unblockable] (pua_icon: \uE41F)
   - 官方描述: "发动前冲攻击时有25%的概率不可防御  // 图标在前冲过程中出现，未触发则不出现"
   - 实现方案:
     dragstrip_dash_unblockable: 前冲攻击起手 25% 概率触发不可防御，无视敌方格挡。金黄图标 (E41F)。

3. [ID: 3525 | 被动 - 修复 / Repair] (pua_icon: \uE503)
   - 官方描述: "成功叠加3层流血时，停止对手流血减益并触发修复，4秒内回复5%的最大生命值。"
   - 实现方案:
     a) dragstrip_bleed_stack_heal: 对手叠加达到 3 层流血时触发战地修复，4 秒回复 5% 最大生命值。翠绿图标 (E503)。
     b) dragstrip_bleed_stack_consume: 清除并停止对手身上累积的流血减益。

4. [ID: 3526 | 特殊技 1 - 流血 / SP1 Bleed] (pua_icon: \uE401)
   - 官方描述: "80%概率施加流血，造成攻击力70%的伤害，持续7秒。"
   - 实现方案:
     dragstrip_sp1_bleed: SP1 命中 80% 概率施加 7 秒流血 (70% ATK 伤害)。

5. [ID: 3527 | 特殊技 1 - 暴击几率 / SP1 Crit Rate] (pua_icon: \uE40D)
   - 官方描述: "最后一击命中后，增加50%的暴击几率，持续5秒。"
   - 实现方案:
     dragstrip_sp1_crit_rate: SP1 最后一击命中获得 50% 暴击几率提升，持续 5 秒。

6. [ID: 3528 | 特殊技 2 - 暴击几率 / SP2 Crit Rate] (pua_icon: \uE40D)
   - 官方描述: "最后一击命中后，增加80%的暴击几率，持续8秒。"
   - 实现方案:
     dragstrip_sp2_crit_rate: SP2 最后一击命中获得 80% 暴击几率提升，持续 8 秒。

7. [ID: 3529 | 特殊技 2 - 规避克制 / SP2 Anti Evade] (pua_icon: \uE92A)
   - 官方描述: "最后一击命中后，施加规避克制，完全禁止对方规避，持续8秒。"
   - 实现方案:
     dragstrip_sp2_anti_evade: SP2 最后一击命中对目标施加规避克制，完全封印对手近战与远程规避 8 秒。

8. [ID: 3530 | 特殊技 3 - 双层流血 / SP3 Double Bleed] (pua_icon: \uE401)
   - 官方描述: "技能完成时施加2层流血，每层造成攻击力70%的伤害，持续7秒。"
   - 实现方案:
     dragstrip_sp3_bleed_1 & dragstrip_sp3_bleed_2: SP3 完成时向目标施加 2 层独立流血，每层 70% ATK 持续 7 秒。

9. [ID: 3531 | 特殊技 3 - 能量锁定 / SP3 Power Lock] (pua_icon: \uE523)
   - 官方描述: "技能完成时100%概率触发能量锁定，阻止对方获得能量，持续5秒"
   - 实现方案:
     dragstrip_sp3_power_lock: SP3 完成时 100% 概率对目标施加 5 秒能量锁定。
-----------------------------------------------------------------------------
"""

from ..core import (
    AbilityColor,
    make_bleed_statmod,
    make_crit_rate_statmod,
    make_heal_statmod,
    make_power_leak_statmod,
    make_power_lock_statmod,
    make_remove_statmod,
    make_statmod_appearance,
    validate_statmod,
    validate_appear,
)
from ..registry import register_bot

BOT_ID = "dragstrip_gs_deluxe2016"


@register_bot(BOT_ID, name_zh="抢劫", desc="飞虎队狡黠赛车手，前冲突袭不可防御、叠满3层流血自愈修复、SP1/SP2暴击几率爆发、SP2规避克制与SP3能量锁定")
def build_dragstrip_abilities(base_hp: float = 34850.0, base_atk: float = 3485.0):
    """
    根据基准属性生成抢劫全部专属能力修饰器。
    基准 5星50级 HP = 34850.0, ATK = 3485.0
    """
    mods = {}
    appears = {}
    buffs = {
        # 规避克制 Debuff
        "anti_evade": {
            "id": "anti_evade",
            "iconTexture": "",
            "image": "",
            "images3": False,
            "modeAvail": [],
            "scope": "global",
            "valueType": "absolute",
            "displayValue": 1.0,
            "c": 1,
            "value": 1.0,
            "buffType": "debuff",
            "group": "anti_evade",
            "p": {"disable_evade": True},
            "hasDuration": True,
            "e": 0,
            "time": {"amount": 8.0},
            "loc_name": "anti_evade",
            "loc_desc": "anti_evade",
        },
    }

    # -------------------------------------------------------------------------
    # 1. [ID: 3516] 觉醒技 - 卑鄙胜者 (重击命中45%吸取10%能量 + 40% ATK流血 5s)
    # -------------------------------------------------------------------------
    # (1) 窃取能量 (扣除对手 10% 最大能量 = 30 Mana)
    m_sig_steal, a_sig_steal = make_power_leak_statmod(
        mod_id="dragstrip_sig_power_steal",
        duration=0.5,
        drain_bars=0.10,
        chance=0.45,
        trigger="onHit",
        trigger_scope="level=Heavy",
        appr_id="appr_dragstrip_power_steal",
        callout_text="卑鄙胜者",
        pua_icon="\uE607",
        color_hex=AbilityColor.RED_DEBUFF_TC,
        gradient_bottom=AbilityColor.RED_DEBUFF_GB,
    )
    mods.update(m_sig_steal)
    appears.update(a_sig_steal)

    # (2) 施加流血 40% ATK 5.0s
    m_sig_bleed, a_sig_bleed = make_bleed_statmod(
        mod_id="dragstrip_sig_bleed",
        duration=5.0,
        total_dmg=float(round(base_atk * 0.40)),
        chance=0.45,
        trigger="onHit",
        trigger_scope="level=Heavy",
        appr_id="appr_dragstrip_bleed",
        callout_text="流血",
        pua_icon="\uE401",
        color_hex=AbilityColor.RED_DEBUFF_TC,
        gradient_bottom=AbilityColor.RED_DEBUFF_GB,
    )
    mods.update(m_sig_bleed)
    appears.update(a_sig_bleed)

    # -------------------------------------------------------------------------
    # 2. [ID: 3524] 被动 - 不可防御 (前冲攻击 25% 概率不可防御)
    # -------------------------------------------------------------------------
    appr_dash_unblockable = make_statmod_appearance(
        appr_id="appr_dragstrip_dash_unblockable",
        callout_text="不可防御",
        desc="前冲攻击势不可挡，强行穿透对手格挡",
        short_desc="不可防御",
        pua_icon="\uE41F",
        color=AbilityColor.YELLOW_STATUS,
        show_callout=True,
    )
    mod_dash_unblockable = {
        "id": "dragstrip_dash_unblockable",
        "t": "unstoppable",
        "tm": "",
        "tr": ["onPlayerStateEnter"],
        "uit": ["onPlayerStateEnter"],
        "pri": 1,
        "trm": 0.0,
        "trs": "state=DashAttack",
        "trr": "repeat",
        "c": 0.25,
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
        "a": ["appr_dragstrip_dash_unblockable"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_appear(appr_dash_unblockable)
    validate_statmod(mod_dash_unblockable)
    appears[appr_dash_unblockable["id"]] = appr_dash_unblockable
    mods[mod_dash_unblockable["id"]] = mod_dash_unblockable

    # -------------------------------------------------------------------------
    # 3. [ID: 3525] 被动 - 修复 (成功叠加3层流血时停止流血，4s恢复5%最大生命)
    # -------------------------------------------------------------------------
    heal_amount = float(round(base_hp * 0.05))
    m_heal, a_heal = make_heal_statmod(
        mod_id="dragstrip_bleed_stack_heal",
        duration=4.0,
        heal_amount=heal_amount,
        chance=1.0,
        trigger="onHit",
        trigger_scope="opp.status=dmg_bleed>=3",
        appr_id="appr_dragstrip_repair",
        callout_text="修复",
        pua_icon="\uE503",
        color_hex=AbilityColor.GREEN_HEALTH_TC,
        gradient_bottom=AbilityColor.GREEN_HEALTH_GB,
    )
    mods.update(m_heal)
    appears.update(a_heal)

    # 停止对手流血减益
    m_remove, a_remove = make_remove_statmod(
        mod_id="dragstrip_bleed_stack_consume",
        target_mod_id="dmg_bleed",
        trigger="onHit",
        trigger_scope="opp.status=dmg_bleed>=3",
        callout_text="修复",
        show_callout=False,
    )
    mods.update(m_remove)
    appears.update(a_remove)

    # -------------------------------------------------------------------------
    # 4. [ID: 3526] 特殊技 1 - 流血 (80% 几率 70% ATK 7s)
    # -------------------------------------------------------------------------
    m_sp1_bleed, a_sp1_bleed = make_bleed_statmod(
        mod_id="dragstrip_sp1_bleed",
        duration=7.0,
        total_dmg=float(round(base_atk * 0.70)),
        chance=0.80,
        trigger="onSpecial1Hit",
        trigger_scope="",
        appr_id="appr_dragstrip_bleed",
        callout_text="流血",
        pua_icon="\uE401",
        color_hex=AbilityColor.RED_DEBUFF_TC,
        gradient_bottom=AbilityColor.RED_DEBUFF_GB,
    )
    mods.update(m_sp1_bleed)
    appears.update(a_sp1_bleed)

    # -------------------------------------------------------------------------
    # 5. [ID: 3527] 特殊技 1 - 暴击几率 (+50% 暴击几率持续 5s)
    # -------------------------------------------------------------------------
    m_sp1_crit, a_sp1_crit = make_crit_rate_statmod(
        mod_id="dragstrip_sp1_crit_rate",
        duration=5.0,
        crit_bonus=0.50,
        chance=1.0,
        trigger="onSpecial1Hit",
        trigger_scope="dmgFlags=LastHit",
        appr_id="appr_dragstrip_sp1_crit_rate",
        callout_text="暴击几率",
        pua_icon="\uE40D",
        color_hex="F59E0B",
        gradient_bottom="D97706",
    )
    mods.update(m_sp1_crit)
    appears.update(a_sp1_crit)

    # -------------------------------------------------------------------------
    # 6. [ID: 3528] 特殊技 2 - 暴击几率 (+80% 暴击几率持续 8s)
    # -------------------------------------------------------------------------
    m_sp2_crit, a_sp2_crit = make_crit_rate_statmod(
        mod_id="dragstrip_sp2_crit_rate",
        duration=8.0,
        crit_bonus=0.80,
        chance=1.0,
        trigger="onSpecial2Hit",
        trigger_scope="dmgFlags=LastHit",
        appr_id="appr_dragstrip_sp2_crit_rate",
        callout_text="暴击几率",
        pua_icon="\uE40D",
        color_hex="F59E0B",
        gradient_bottom="D97706",
    )
    mods.update(m_sp2_crit)
    appears.update(a_sp2_crit)

    # -------------------------------------------------------------------------
    # 7. [ID: 3529] 特殊技 2 - 规避克制 (最后一击完全禁止对手规避持续 8s)
    # -------------------------------------------------------------------------
    appr_anti_evade = make_statmod_appearance(
        appr_id="appr_dragstrip_anti_evade",
        callout_text="规避克制",
        desc="完全禁止对手规避，持续8秒",
        short_desc="封印规避",
        pua_icon="\uE92A",
        color=AbilityColor.RED_DEBUFF,
        show_callout=True,
    )
    mod_anti_evade = {
        "id": "dragstrip_sp2_anti_evade",
        "t": "anti_evade",
        "tm": "",
        "tr": ["onSpecial2Hit"],
        "uit": ["onSpecial2Hit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "dmgFlags=LastHit",
        "trr": "repeat",
        "c": 1.0,
        "m": 1.0,
        "d": 8.0,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "anti_evade",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_dragstrip_anti_evade"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_appear(appr_anti_evade)
    validate_statmod(mod_anti_evade)
    appears[appr_anti_evade["id"]] = appr_anti_evade
    mods[mod_anti_evade["id"]] = mod_anti_evade

    # -------------------------------------------------------------------------
    # 8. [ID: 3530] 特殊技 3 - 2层流血 (每层 70% ATK 持续 7s)
    # -------------------------------------------------------------------------
    # 第 1 层流血
    m_sp3_bleed1, a_sp3_bleed1 = make_bleed_statmod(
        mod_id="dragstrip_sp3_bleed_1",
        duration=7.0,
        total_dmg=float(round(base_atk * 0.70)),
        chance=1.0,
        trigger="onSpecial3Expiry",
        trigger_scope="",
        appr_id="appr_dragstrip_bleed",
        callout_text="流血",
        pua_icon="\uE401",
        color_hex=AbilityColor.RED_DEBUFF_TC,
        gradient_bottom=AbilityColor.RED_DEBUFF_GB,
    )
    mods.update(m_sp3_bleed1)
    appears.update(a_sp3_bleed1)

    # 第 2 层流血
    m_sp3_bleed2, _ = make_bleed_statmod(
        mod_id="dragstrip_sp3_bleed_2",
        duration=7.0,
        total_dmg=float(round(base_atk * 0.70)),
        chance=1.0,
        trigger="onSpecial3Expiry",
        trigger_scope="",
        appr_id="appr_dragstrip_bleed",
        callout_text="流血",
        pua_icon="\uE401",
        color_hex=AbilityColor.RED_DEBUFF_TC,
        gradient_bottom=AbilityColor.RED_DEBUFF_GB,
    )
    mods.update(m_sp3_bleed2)

    # -------------------------------------------------------------------------
    # 9. [ID: 3531] 特殊技 3 - 能量锁定 (技能完成 100% 触发能量锁定 5s)
    # -------------------------------------------------------------------------
    m_sp3_lock, a_sp3_lock = make_power_lock_statmod(
        mod_id="dragstrip_sp3_power_lock",
        duration=5.0,
        chance=1.0,
        trigger="onSpecial3Expiry",
        trigger_scope="",
        appr_id="appr_dragstrip_power_lock",
        callout_text="能量锁定",
        pua_icon="\uE523",
        color_hex=AbilityColor.RED_DEBUFF_TC,
        gradient_bottom=AbilityColor.RED_DEBUFF_GB,
    )
    mods.update(m_sp3_lock)
    appears.update(a_sp3_lock)

    return mods, appears, buffs
