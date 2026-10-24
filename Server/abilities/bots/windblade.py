#!/usr/bin/env python3
"""
Bot Ability Implementation: 风刃 (Windblade)
===========================================
Bot ID: windblade_gs
阵营: 汽车人 (Autobot) | 职业: 侦察兵 (Scout)

【官方技能真理源对照 (来自 Upstash KV 聚合 78 Priorities 清单)】：
-----------------------------------------------------------------------------
1. [被动 - 剑刃暴击流血] (ID: 2905, pua_icon: 0xe401, category: passive)
   - 官方描述: "近战（包括近战普通攻击和重击）出暴击时，有66%的概率触发流血，造成攻击力68%的伤害，持续4秒。"
   - 实现方案:
     windblade_crit_bleed: 触发 onCrit，限制 level=Light,Medium,Heavy，造成 68% ATK 流血伤害持续 4.0 秒。呼出文字: "流血"。

2. [被动 - 剑刃暴击率] (ID: 2907, pua_icon: 0xe40d, category: passive)
   - 官方描述: "使用剑刃攻击时暴击率增加25%。//包括所有近战攻击，S1和S2"
   - 实现方案:
     windblade_blade_crit_rate: 常驻被动 (always)，自身暴击率提高 25%。呼出文字: "剑刃专注"。

3. [觉醒技 - 决心] (ID: 2908, pua_icon: 0xe40d, category: signature)
   - 官方描述: "根据对手失去的生命值提高暴击率，最高提升25% (对手生命值50%时提升12.5%)"
   - 实现方案:
     windblade_signature_resolution: 觉醒常驻机制 (always)，呼出文字: "决心"，
     配合 Native C (skill_windblade.c) 按对手已损生命值百分比动态注入最高 25% 暴击加成。

4. [被动 - 重击远程穿透] (ID: 2919, pua_icon: 0xe518, category: passive)
   - 官方描述: "重击全程不会被远程普通攻击和远程重击击中。//对方的远程普通攻击和远程重击会直接从风刃身边飞过，这个过程显示一个黄色的图标，重击完成后消失。"
   - 实现方案:
     windblade_heavy_range_immune: 重击期间获得黄色校准/穿透增益，无视并规避所有远程攻击。

5. [被动 - 流血远程眩晕] (ID: 2920, pua_icon: 0xe605, category: passive)
   - 官方描述: "如果对手正处于流血状态，远程攻击命中有35%的概率造成眩晕，持续1.5秒"
   - 实现方案:
     windblade_bleed_remote_stun: 触发 onHit，限制 level=Ranged 且对手处于流血状态 (opponent:status=dmg_bleed)，35% 几率施加 1.5 秒眩晕。呼出文字: "眩晕"。

6. [特殊技1 - 能量增益驱散] (ID: 2909, pua_icon: 0xe950, category: sp1)
   - 官方描述: "如果对手身上有能量增益，则全部驱散，并施加攻击力80%的即时伤害。"
   - 实现方案:
     windblade_sp1_power_nullify: 触发 onHit，限制 level=Special1，驱散对手所有能量增益，并结算 80% ATK 瞬伤。呼出文字: "驱散"。

7. [特殊技1 - 风暴喷发] (ID: 2921, pua_icon: 0xe914, category: sp1)
   - 官方描述: "最后一击施加震击，造成攻击力60%的伤害，持续6秒。//“风暴喷发”是弹出字样，实际加载的效果就是震击。"
   - 实现方案:
     windblade_sp1_shock: 触发 onHit，限制 level=Special1 最后一击，100% 几率造成 6.0 秒震击 (造成 60% ATK 能量伤害)。呼出文字: "风暴喷发"。

8. [特殊技2 - 护甲穿透] (ID: 2910, pua_icon: 0xe409, category: sp2)
   - 官方描述: "最后一击命中后，获得6秒的的护甲穿透增益，所有攻击无视对方100%的护甲值。//图标用黄色"
   - 实现方案:
     windblade_sp2_armor_pierce: 触发 onHit，限制 level=Special2 最后一击，赋予风刃自身 6.0 秒黄色护甲穿透增益。呼出文字: "护甲穿透"。

9. [特殊技3 - 眩晕] (ID: 2922, pua_icon: 0xe605, category: sp3)
   - 官方描述: "技能完成后，35%概率施加眩晕，持续3秒"
   - 实现方案:
     windblade_sp3_stun: 触发 onHit，限制 level=Special3，35% 几率造成 3.0 秒眩晕。呼出文字: "眩晕"。
-----------------------------------------------------------------------------
"""

from ..core import (
    AbilityColor,
    make_bleed_statmod,
    make_shock_statmod,
    make_stun_statmod,
    make_statmod_appearance,
    make_condition_scope,
    validate_statmod,
    validate_appear,
    validate_color_code,
)
from ..registry import register_bot

BOT_ID = "windblade_gs"


@register_bot(BOT_ID, name_zh="风刃", desc="侦察兵，高暴击流血、决心残血斩杀、重击远程穿透、SP1驱散与风暴喷发、SP2护甲穿透")
def build_windblade_abilities(base_hp: float = 26794.0, base_atk: float = 2583.0):
    """
    根据基准属性生成风刃专属全套能力修饰器。
    基准 5星50级 ATK = 2583.0, HP = 26794.0
    """
    mods = {}
    appears = {}

    # -------------------------------------------------------------------------
    # 1. 被动：近战暴击流血 4.0s DOT (68% ATK, 66% 概率) (ID: 2905 - 既有保留)
    # -------------------------------------------------------------------------
    total_bleed_dmg = float(round(base_atk * 0.68, 2))
    buffs = {
        "dmg_bleed": {
            "id": "dmg_bleed",
            "iconTexture": "",
            "image": "",
            "images3": False,
            "modeAvail": [],
            "scope": "global",
            "valueType": "absolute",
            "displayValue": total_bleed_dmg,
            "c": 1,
            "value": total_bleed_dmg,
            "buffType": "damage",
            "group": "dmg_bleed",
            "p": {"damage_type": "bleed"},
            "hasDuration": True,
            "e": 0,
            "time": {"amount": 4.0},
            "loc_name": "bleed",
            "loc_desc": "bleed",
        },
    }

    m_bleed, a_bleed = make_bleed_statmod(
        mod_id="windblade_crit_bleed",
        duration=4.0,
        total_dmg=total_bleed_dmg,
        chance=0.66,
        trigger="onCrit",
        trigger_scope="level=Light,Medium,Heavy",
        appr_id="appr_windblade_bleed",
        callout_text="流血",
        buff_id="dmg_bleed",
    )
    mods.update(m_bleed)
    appears.update(a_bleed)

    # -------------------------------------------------------------------------
    # 2. 被动：剑刃暴击率 (ID: 2907, PUA: 0xE40D) - 剑刃攻击暴击率增加 25%
    # -------------------------------------------------------------------------
    appr_blade_crit = make_statmod_appearance(
        appr_id="appr_windblade_blade_crit",
        callout_text="剑刃专注",
        desc="使用剑刃攻击时暴击率增加25%",
        short_desc="剑刃暴击率",
        pua_icon="\uE40D",
        color=AbilityColor.ORANGE_DAMAGE,
        show_callout=False,
        active_desc="剑刃攻击暴击率提升25%",
    )
    mod_blade_crit = {
        "id": "windblade_blade_crit_rate",
        "t": "crit_rate",
        "tm": "",
        "tr": ["always"],
        "uit": ["always"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.25,
        "d": 0.0,
        "s": "none",
        "ta": "self",
        "mt": "passive",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "windblade_crit",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_windblade_blade_crit"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_blade_crit)
    mods["windblade_blade_crit_rate"] = mod_blade_crit
    appears["appr_windblade_blade_crit"] = appr_blade_crit

    # -------------------------------------------------------------------------
    # 3. 觉醒技：决心 (ID: 2908, PUA: 0xE40D) - 根据对手失去生命值提高暴击率 (最高 25%)
    # -------------------------------------------------------------------------
    appr_resolution = make_statmod_appearance(
        appr_id="appr_windblade_resolution",
        callout_text="决心",
        desc="根据对手失去的生命值提高暴击率，最高提升25%",
        short_desc="决心",
        pua_icon="\uE40D",
        color={"tc": "A855F7", "gt": "A855F7", "gb": "9333EA"},
        show_callout=True,
        active_desc="决心生效中：随敌方残血动态提升暴击率",
    )
    mod_resolution = {
        "id": "windblade_signature_resolution",
        "t": "passive",
        "tm": "",
        "tr": ["always"],
        "uit": ["always"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.25,
        "d": 0.0,
        "s": "none",
        "ta": "self",
        "mt": "passive",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "windblade_resolution",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_windblade_resolution"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_resolution)
    mods["windblade_signature_resolution"] = mod_resolution
    appears["appr_windblade_resolution"] = appr_resolution

    # -------------------------------------------------------------------------
    # 4. 被动：重击远程穿透 (ID: 2919, PUA: 0xE518) - 重击全程免疫远程普攻与远程重击
    # -------------------------------------------------------------------------
    appr_heavy_immune = make_statmod_appearance(
        appr_id="appr_windblade_heavy_range_immune",
        callout_text="",
        desc="重击全程不会被远程普通攻击和远程重击击中",
        short_desc="远程穿透",
        pua_icon="\uE518",
        color=AbilityColor.YELLOW_STATUS,
        show_callout=False,
        active_desc="重击蓄力中：远程攻击穿透免疫",
    )
    mod_heavy_immune = {
        "id": "windblade_heavy_range_immune",
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
        "d": 0.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "windblade_heavy_immune",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_windblade_heavy_range_immune"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_heavy_immune)
    mods["windblade_heavy_range_immune"] = mod_heavy_immune
    appears["appr_windblade_heavy_range_immune"] = appr_heavy_immune

    # -------------------------------------------------------------------------
    # 5. 被动：流血远程眩晕 1.5s (ID: 2920, PUA: 0xE605, 35% 几率)
    # -------------------------------------------------------------------------
    m_stun_bleed, a_stun_bleed = make_stun_statmod(
        mod_id="windblade_bleed_remote_stun",
        duration=1.5,
        chance=0.35,
        trigger="onHit",
        trigger_scope=make_condition_scope(level="Ranged", extra="opponent:status=dmg_bleed"),
        target_actor="opponent",
        appr_id="appr_windblade_remote_stun",
        callout_text="眩晕",
        pua_icon="\uE605",
        color_hex="FFE000",
        gradient_bottom="FFAA00",
        show_callout=True,
    )
    mods.update(m_stun_bleed)
    appears.update(a_stun_bleed)

    # -------------------------------------------------------------------------
    # 6. SP1：能量增益驱散并施加 80% ATK 瞬伤 (ID: 2909, PUA: 0xE950)
    # -------------------------------------------------------------------------
    sp1_nullify_dmg = float(round(base_atk * 0.80, 2))
    appr_sp1_nullify = make_statmod_appearance(
        appr_id="appr_windblade_sp1_power_nullify",
        callout_text="驱散",
        desc=f"驱散对手所有能量增益，并施加{int(sp1_nullify_dmg)}点即时伤害",
        short_desc="能量驱散",
        pua_icon="\uE950",
        color=AbilityColor.BLUE_DEFENSE,
        show_callout=False,
        active_desc="驱散目标能量增益",
    )
    mod_sp1_nullify = {
        "id": "windblade_sp1_power_nullify",
        "t": "remove",
        "tm": "power_gain",
        "tr": ["onHit"],
        "uit": ["onHit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "level=Special1",
        "trr": "repeat",
        "c": 1.0,
        "m": sp1_nullify_dmg,
        "d": 0.0,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "windblade_nullify",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_windblade_sp1_power_nullify"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_sp1_nullify)
    mods["windblade_sp1_power_nullify"] = mod_sp1_nullify
    appears["appr_windblade_sp1_power_nullify"] = appr_sp1_nullify

    # -------------------------------------------------------------------------
    # 7. SP1：风暴喷发 6.0s 震击 DOT (60% ATK, ID: 2921, PUA: 0xE914)
    # -------------------------------------------------------------------------
    sp1_shock_dmg = float(round(base_atk * 0.60, 2))
    buffs["dmg_shock"] = {
        "id": "dmg_shock",
        "iconTexture": "",
        "image": "",
        "images3": False,
        "modeAvail": [],
        "scope": "global",
        "valueType": "absolute",
        "displayValue": sp1_shock_dmg,
        "c": 1,
        "value": sp1_shock_dmg,
        "buffType": "damage",
        "group": "dmg_shock",
        "p": {"damage_type": "shock"},
        "hasDuration": True,
        "e": 0,
        "time": {"amount": 6.0},
        "loc_name": "shock",
        "loc_desc": "shock",
    }
    m_shock, a_shock = make_shock_statmod(
        mod_id="windblade_sp1_shock",
        duration=6.0,
        total_dmg=sp1_shock_dmg,
        chance=1.0,
        trigger="",  # 程序化触发：完全由 Native C 在最后一击精准判定，防止 Unity 引擎在多段 hit 重复触发
        trigger_scope="",
        appr_id="appr_windblade_sp1_shock",
        callout_text="风暴喷发",
        pua_icon="\uE914",
        color_hex=AbilityColor.RED_DEBUFF_TC,
        gradient_bottom=AbilityColor.RED_DEBUFF_GB,
        show_callout=True,
    )
    m_shock["windblade_sp1_shock"]["tr"] = []
    m_shock["windblade_sp1_shock"]["uit"] = []
    mods.update(m_shock)
    appears.update(a_shock)

    # -------------------------------------------------------------------------
    # 8. SP2：护甲穿透 6.0s 增益 (ID: 2910, PUA: 0xE409) - 100% 无视对手护甲
    # -------------------------------------------------------------------------
    appr_armor_pierce = make_statmod_appearance(
        appr_id="appr_windblade_sp2_armor_pierce",
        callout_text="护甲穿透",
        desc="所有攻击无视对方100%的护甲值，持续6秒",
        short_desc="护甲穿透",
        pua_icon="\uE409",
        color={"tc": "F59E0B", "gt": "F59E0B", "gb": "D97706"},
        show_callout=True,
        active_desc="护甲穿透生效中：所有攻击无视100%护甲",
    )
    mod_armor_pierce = {
        "id": "windblade_sp2_armor_pierce",
        "t": "armor_pierce",
        "tm": "",
        "tr": ["onHit"],
        "uit": ["onHit"],
        "pri": 0,
        "trm": 0.0,
        "trs": make_condition_scope(level="Special2", is_last_hit=True),
        "trr": "repeat",
        "c": 1.0,
        "m": 1.0,  # 100% 穿透
        "d": 6.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "windblade_pierce",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_windblade_sp2_armor_pierce"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_armor_pierce)
    mods["windblade_sp2_armor_pierce"] = mod_armor_pierce
    appears["appr_windblade_sp2_armor_pierce"] = appr_armor_pierce

    # -------------------------------------------------------------------------
    # 9. SP3：眩晕 3.0s (ID: 2922, PUA: 0xE605, 35% 几率)
    # -------------------------------------------------------------------------
    m_sp3_stun, a_sp3_stun = make_stun_statmod(
        mod_id="windblade_sp3_stun",
        duration=3.0,
        chance=0.35,
        trigger="onHit",
        trigger_scope=make_condition_scope(level="Special3", is_last_hit=True),
        target_actor="opponent",
        appr_id="appr_windblade_sp3_stun",
        callout_text="眩晕",
        pua_icon="\uE605",
        color_hex="FFE000",
        gradient_bottom="FFAA00",
        show_callout=True,
    )
    mods.update(m_sp3_stun)
    appears.update(a_sp3_stun)

    return mods, appears, buffs
