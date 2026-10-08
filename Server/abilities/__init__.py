#!/usr/bin/env python3
"""
TFTF Combat Ability & Buff System Package
=========================================
统一对外暴露战斗能力系统的各项构建接口与数据，保持与 gamedata.py 的 100% 兼容性。
"""

from .sp_callouts import BOT_SP_MAP, build_sp_callout_appears, build_sp_callout_statmods
from .registry import (
    register_bot,
    load_all_bots,
    get_registered_bots,
    get_bot_mod_ids,
    collect_all_bot_statmods_and_appears,
)


def build_buffs_config():
    """定义战斗中各类 Buff 的堆叠与血条下 UI 挂件显示策略。"""
    groups_data = {
        # 跳字累加器：常驻不可见
        "floating_text": {"stackable": True, "active_display": False},
        "floating_text_dmg": {"stackable": True, "active_display": False},
        "floating_text_heal": {"stackable": True, "active_display": False},
        # SP 技能呼出文字组：仅触发 Callout Text，不在血条下显示 Buff 图标
        "sp_callout": {"stackable": True, "active_display": False},
        # 流血类 Debuff：可堆叠，在敌人血条下方显示倒计时圆环图标
        "dmg_bleed": {"stackable": True, "active_display": True},
        # 直接伤害：不显示血条下方图标
        "dmg_direct": {"stackable": True, "active_display": False},
        # 不可阻挡 (霸体) Buff：不可堆叠，在血条下方显示倒计时圆环图标
        "unstoppable": {"stackable": False, "active_display": True},
        # 动作/特效播放 Buff：不显示血条下方图标
        "play_move": {"stackable": True, "active_display": False},
        # 移除 Buff 效果器：不显示血条下方图标
        "remove": {"stackable": True, "active_display": False},
        # 远程攻击增益 Buff：正面增益，在血条下方显示倒计时圆环图标，可被驱散
        "ranged_buff": {"stackable": True, "active_display": True},
        # 震击类 Debuff：可堆叠，在敌人血条下方显示倒计时圆环图标
        "dmg_shock": {"stackable": True, "active_display": True},
        # 能量流失 Debuff：可堆叠，在敌人血条下方显示倒计时圆环图标
        "power_leak": {"stackable": True, "active_display": True},
        # 眩晕控制 Debuff：不可堆叠，在敌人血条下方显示倒计时圆环图标
        "stun": {"stackable": False, "active_display": True},
        # 驱散效果器：瞬时结算，不显示血条下方图标
        "nullify": {"stackable": True, "active_display": False},
        # 近战规避 Buff：在血条下方显示绿色倒计时/常驻圆环图标
        "evade_melee": {"stackable": False, "active_display": True},
        # 远程规避 Buff：在血条下方显示绿色倒计时/常驻圆环图标
        "evade_ranged": {"stackable": False, "active_display": True},
        # 暴击几率增益 Buff：在血条下方显示金色倒计时圆环图标
        "crit_rate": {"stackable": True, "active_display": True},
        # 护甲增益 Buff：在血条下方显示蓝色倒计时圆环图标
        "armor_up": {"stackable": True, "active_display": True},
        # 破甲减益 Debuff：在敌人血条下方显示红色倒计时圆环图标
        "armor_break": {"stackable": True, "active_display": True},
        # 攻击力增益 Buff：在血条下方显示金色倒计时圆环图标
        "attack_buff": {"stackable": True, "active_display": True},
        # 燃烧类 Debuff：可堆叠，在敌人血条下方显示倒计时圆环图标
        "dmg_burn": {"stackable": True, "active_display": True},
    }
    return {
        "groups": groups_data,
        "groupings": groups_data,
    }


def build_buffs_set():
    """全局 Buff 模板库。每个 id 对应 Damage_BuffEffect 或 FloatingText_BuffEffect 或 Attribute_BuffEffect。"""
    global_buffs = {
        # 不可阻挡 (霸体) Buff：激活时底层 _unstoppable != 0，彻底跳过 ApplyHitStun 受创硬直
        "unstoppable": {
            "id": "unstoppable",
            "iconTexture": "",
            "image": "",
            "images3": False,
            "modeAvail": [],
            "scope": "global",
            "valueType": "absolute",
            "displayValue": 1.0,
            "c": 1,
            "value": 1.0,
            "buffType": "unstoppable",
            "group": "unstoppable",
            "p": {},
            "hasDuration": True,
            "e": 0,
            "time": {"amount": 4.0},
            "loc_name": "unstoppable",
            "loc_desc": "unstoppable",
        },
        # 动作/光环播放 Buff：触发时调用 MoveSequencer.EnterMove，过期调用 ExitMove
        "play_move": {
            "id": "play_move",
            "iconTexture": "",
            "image": "",
            "images3": False,
            "modeAvail": [],
            "scope": "global",
            "valueType": "absolute",
            "displayValue": 0.0,
            "c": 1,
            "value": 0.0,
            "buffType": "play_move",
            "group": "play_move",
            "p": {},
            "hasDuration": True,
            "e": 0,
            "time": {"amount": 4.0},
            "loc_name": "play_move",
            "loc_desc": "play_move",
        },
        # 移除 Buff 效果器：根据 tm 指定的 StatModifier ID 移除对应 Buff
        "remove": {
            "id": "remove",
            "iconTexture": "",
            "image": "",
            "images3": False,
            "modeAvail": [],
            "scope": "global",
            "valueType": "absolute",
            "displayValue": 0.0,
            "c": 1,
            "value": 0.0,
            "buffType": "remove",
            "group": "remove",
            "p": {},
            "hasDuration": False,
            "e": 0,
            "time": {"amount": 0.0},
            "loc_name": "remove",
            "loc_desc": "remove",
        },
        # 通用 SP 技能呼出 Buff：触发时向对应角色侧派发 1 秒技能名 Callout
        "sp_callout": {
            "id": "sp_callout",
            "iconTexture": "",
            "image": "",
            "images3": False,
            "modeAvail": [],
            "scope": "global",
            "valueType": "absolute",
            "displayValue": 0.0,
            "c": 1,
            "value": 0.0,
            "buffType": "buff",
            "group": "sp_callout",
            "p": {},
            "hasDuration": True,
            "e": 0,
            "time": {"amount": 1.0},
            "loc_name": "sp_callout",
            "loc_desc": "sp_callout",
        },
        # 伤害跳字收集器：捕获 _ftd 变量累加值，弹出红色跳字
        "floating_text": {
            "id": "floating_text",
            "iconTexture": "",
            "image": "",
            "images3": False,
            "modeAvail": [],
            "scope": "global",
            "valueType": "absolute",
            "displayValue": 0.0,
            "c": 1,
            "value": 0.0,
            "buffType": "floating_text",
            "group": "floating_text",
            "p": {"key": "_ftd", "style": 0},
            "hasDuration": False,
            "e": 0,
            "time": {"amount": 0},
            "loc_name": "floating_text",
            "loc_desc": "floating_text",
        },
        # 伤害跳字收集器 (dmg)：红色跳字
        "floating_text_dmg": {
            "id": "floating_text_dmg",
            "iconTexture": "",
            "image": "",
            "images3": False,
            "modeAvail": [],
            "scope": "global",
            "valueType": "absolute",
            "displayValue": 0.0,
            "c": 1,
            "value": 0.0,
            "buffType": "floating_text",
            "group": "floating_text_dmg",
            "p": {"key": "_ftd", "style": 0},
            "hasDuration": False,
            "e": 0,
            "time": {"amount": 0},
            "loc_name": "floating_text_dmg",
            "loc_desc": "floating_text_dmg",
        },
        # 治疗跳字收集器：捕获 _fth 变量累加值，弹出绿色跳字
        "floating_text_heal": {
            "id": "floating_text_heal",
            "iconTexture": "",
            "image": "",
            "images3": False,
            "modeAvail": [],
            "scope": "global",
            "valueType": "absolute",
            "displayValue": 0.0,
            "c": 1,
            "value": 0.0,
            "buffType": "floating_text",
            "group": "floating_text_heal",
            "p": {"key": "_fth", "style": 0},
            "hasDuration": False,
            "e": 0,
            "time": {"amount": 0},
            "loc_name": "floating_text_heal",
            "loc_desc": "floating_text_heal",
        },
        # 远程攻击强化 Buff (支持加伤、提速)
        "ranged_buff": {
            "id": "ranged_buff",
            "iconTexture": "",
            "image": "",
            "images3": False,
            "modeAvail": [],
            "scope": "global",
            "valueType": "multiplier",
            "displayValue": 1.0,
            "c": 1,
            "value": 1.0,
            "buffType": "buff",
            "group": "ranged_buff",
            "p": {},
            "hasDuration": True,
            "e": 0,
            "time": {"amount": 6.5},
            "loc_name": "ranged_buff",
            "loc_desc": "ranged_buff",
        },
        # 震击能量伤害 DOT
        "dmg_shock": {
            "id": "dmg_shock",
            "iconTexture": "",
            "image": "",
            "images3": False,
            "modeAvail": [],
            "scope": "global",
            "valueType": "absolute",
            "displayValue": 0.0,
            "c": 1,
            "value": 0.0,
            "buffType": "damage",
            "group": "dmg_shock",
            "p": {"damage_type": "energy"},
            "hasDuration": True,
            "e": 0,
            "time": {"amount": 6.0},
            "loc_name": "dmg_shock",
            "loc_desc": "dmg_shock",
        },
        # 能量流失扣能 DOT
        "power_leak": {
            "id": "power_leak",
            "iconTexture": "",
            "image": "",
            "images3": False,
            "modeAvail": [],
            "scope": "global",
            "valueType": "absolute",
            "displayValue": 0.0,
            "c": 1,
            "value": 0.0,
            "buffType": "buff",
            "group": "power_leak",
            "p": {"drain_type": "power"},
            "hasDuration": True,
            "e": 0,
            "time": {"amount": 3.0},
            "loc_name": "power_leak",
            "loc_desc": "power_leak",
        },
        # 眩晕硬控
        "stun": {
            "id": "stun",
            "iconTexture": "",
            "image": "",
            "images3": False,
            "modeAvail": [],
            "scope": "global",
            "valueType": "absolute",
            "displayValue": 1.0,
            "c": 1,
            "value": 1.0,
            "buffType": "buff",
            "group": "stun",
            "p": {"action": "incapacitate"},
            "hasDuration": True,
            "e": 0,
            "time": {"amount": 3.0},
            "loc_name": "stun",
            "loc_desc": "stun",
        },
        # 增益驱散效果器
        "nullify": {
            "id": "nullify",
            "iconTexture": "",
            "image": "",
            "images3": False,
            "modeAvail": [],
            "scope": "global",
            "valueType": "absolute",
            "displayValue": 0.0,
            "c": 1,
            "value": 0.0,
            "buffType": "remove",
            "group": "nullify",
            "p": {},
            "hasDuration": False,
            "e": 0,
            "time": {"amount": 0.0},
            "loc_name": "nullify",
            "loc_desc": "nullify",
        },
        # 近战规避 Buff：可规避基础近战与特技近战攻击 (由底层仲裁规避与呼出文字)
        "evade_melee": {
            "id": "evade_melee",
            "iconTexture": "",
            "image": "",
            "images3": False,
            "modeAvail": [],
            "scope": "global",
            "valueType": "absolute",
            "displayValue": 1.0,
            "c": 1,
            "value": 1.0,
            "buffType": "buff",
            "group": "evade_melee",
            "p": {},
            "hasDuration": True,
            "e": 0,
            "time": {"amount": 3.0},
            "loc_name": "evade_melee",
            "loc_desc": "evade_melee",
        },
        # 远程规避 Buff：可规避基础远程与特技远程攻击 (由底层仲裁规避与呼出文字)
        "evade_ranged": {
            "id": "evade_ranged",
            "iconTexture": "",
            "image": "",
            "images3": False,
            "modeAvail": [],
            "scope": "global",
            "valueType": "absolute",
            "displayValue": 1.0,
            "c": 1,
            "value": 1.0,
            "buffType": "buff",
            "group": "evade_ranged",
            "p": {},
            "hasDuration": True,
            "e": 0,
            "time": {"amount": 3.0},
            "loc_name": "evade_ranged",
            "loc_desc": "evade_ranged",
        },
        # 消耗型规避充能 Buff：无倒计时，血条下方常驻绿色圆环图标，触发规避后消耗
        "evade_charge": {
            "id": "evade_charge",
            "iconTexture": "",
            "image": "",
            "images3": False,
            "modeAvail": [],
            "scope": "global",
            "valueType": "absolute",
            "displayValue": 1.0,
            "c": 1,
            "value": 1.0,
            "buffType": "buff",
            "group": "evade_melee",
            "p": {},
            "hasDuration": False,
            "e": 0,
            "time": {"amount": 0.0},
            "loc_name": "evade_charge",
            "loc_desc": "evade_charge",
        },
        # 暴击几率增益 Buff
        "crit_rate": {
            "id": "crit_rate",
            "iconTexture": "",
            "image": "",
            "images3": False,
            "modeAvail": [],
            "scope": "global",
            "valueType": "multiplier",
            "displayValue": 1.0,
            "c": 1,
            "value": 1.0,
            "buffType": "crit_rate",
            "group": "crit_rate",
            "p": {},
            "hasDuration": True,
            "e": 0,
            "time": {"amount": 7.5},
            "loc_name": "crit_rate",
            "loc_desc": "crit_rate",
        },
        # 护甲增益 Buff：提升 ArmorUpModifier，降低受到伤害
        "armor_up": {
            "id": "armor_up",
            "iconTexture": "",
            "image": "",
            "images3": False,
            "modeAvail": [],
            "scope": "global",
            "valueType": "absolute",
            "displayValue": 1.0,
            "c": 1,
            "value": 1.0,
            "buffType": "attribute",
            "group": "armor_up",
            "p": {},
            "hasDuration": True,
            "e": 0,
            "time": {"amount": 5.0},
            "loc_name": "armor_up",
            "loc_desc": "armor_up",
        },
        # 破甲减益 Debuff：提升 ArmorBreakModifier，放大承受伤害并自动移除对方一层护甲
        "armor_break": {
            "id": "armor_break",
            "iconTexture": "",
            "image": "",
            "images3": False,
            "modeAvail": [],
            "scope": "global",
            "valueType": "absolute",
            "displayValue": 1.0,
            "c": 1,
            "value": 1.0,
            "buffType": "armor_break",
            "group": "armor_break",
            "p": {},
            "hasDuration": True,
            "e": 0,
            "time": {"amount": 6.0},
            "loc_name": "armor_break",
            "loc_desc": "armor_break",
        },
        # 攻击力增益 Buff
        "attack_buff": {
            "id": "attack_buff",
            "iconTexture": "",
            "image": "",
            "images3": False,
            "modeAvail": [],
            "scope": "global",
            "valueType": "multiplier",
            "displayValue": 1.0,
            "c": 1,
            "value": 1.0,
            "buffType": "attribute",
            "group": "attack_buff",
            "p": {},
            "hasDuration": True,
            "e": 0,
            "time": {"amount": 6.0},
            "loc_name": "attack_buff",
            "loc_desc": "attack_buff",
        },
        # 燃烧持续能量伤害 DOT
        "dmg_burn": {
            "id": "dmg_burn",
            "iconTexture": "",
            "image": "",
            "images3": False,
            "modeAvail": [],
            "scope": "global",
            "valueType": "absolute",
            "displayValue": 0.0,
            "c": 1,
            "value": 0.0,
            "buffType": "damage",
            "group": "dmg_burn",
            "p": {"damage_type": "energy"},
            "hasDuration": True,
            "e": 0,
            "time": {"amount": 6.0},
            "loc_name": "dmg_burn",
            "loc_desc": "dmg_burn",
        },
    }

    # 动态汇入所有注册机器人提供的额外 Buff 定义
    _, _, extra_buffs = collect_all_bot_statmods_and_appears()
    global_buffs.update(extra_buffs)

    return {
        "globalBuffs": global_buffs,
        "userBuffs": {},
    }


def build_stat_mod_appears():
    """汇总全员 SP 技能呼出外观配置与各机器人专属能力表现配置、英雄招牌与 UI 展示能力。"""
    # 1. 78 位英雄 SP 呼出外观
    appears = build_sp_callout_appears()

    # 2. 各机器人注册的外观
    _, bot_appears, _ = collect_all_bot_statmods_and_appears()
    appears.update(bot_appears)

    # 3. 官方英雄招牌技能外观与 UI 基础能力外观
    try:
        from .. import character_profiles
    except Exception:
        import character_profiles
    appears.update(character_profiles.get_profile_stat_mod_appears())

    # 4. 全局规避呼出文字外观
    appears["appr_evade_callout"] = {
        "id": "appr_evade_callout",
        "a": "规避",
        "s": "",
        "l": "",
        "ss": "",
        "t": "\uE509",
        "f": "",
        "st": "规避",
        "ps": "",
        "pl": "",
        "tc": "10B981",
        "gt": "FFFFFF",
        "gb": "059669",
    }

    return appears


# ---------------------------------------------------------------------------
# 0. 核心引擎底层全局系统修饰器 (受创硬直、伤害/治疗跳字累加器、规避 Callout)
# ---------------------------------------------------------------------------
SYSTEM_GLOBAL_STATMODS = {
    # 全局规避呼出修饰器：规避成功触发时由底层 StatModifierController.ApplyStatModifier 呼出绿色“规避”大字
    "gp_evade_callout": {
        "id": "gp_evade_callout",
        "t": "sp_callout",
        "tm": "",
        "tr": [],
        "uit": [],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.0,
        "d": 1.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 0,
        "g": "",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_evade_callout"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    },
    # 核心受击硬直修饰器 (内置默认)：引擎 ApplyHitStun 强依赖，确保受击方产生硬直与受创后摇
    "gp_hit_stun": {
        "id": "gp_hit_stun",
        "t": "hit_stun",
        "tm": "",
        "tr": [],
        "uit": [],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "none",
        "c": 1.0,
        "m": 1.0,
        # ApplyHitStun 提供运行时硬直时长，此处为 0.5s 保底配置
        "d": 0.5,
        "s": "none",
        "ta": "self",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 0,
        "g": "",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": [],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    },
    # 常驻伤害跳字累加器 (开局 Intro 挂载，持续 -1.0 永久生效)
    "gp_dmg_ft": {
        "id": "gp_dmg_ft",
        "t": "floating_text",
        "tm": "v=_ftd;s=7",
        "tr": ["onIntroStart"],
        "uit": [],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "update",
        "c": 1.0,
        "m": 1.0,
        "d": -1.0,
        "s": "none",
        "ta": "self",
        "mt": "passive",
        "v": "",
        "ms": "",
        "st": 0,
        "g": "",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": [],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    },
    # 常驻治疗跳字累加器
    "gp_heal_ft": {
        "id": "gp_heal_ft",
        "t": "floating_text",
        "tm": "v=_fth;s=6",
        "tr": ["onIntroStart"],
        "uit": [],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "update",
        "c": 1.0,
        "m": 1.0,
        "d": -1.0,
        "s": "none",
        "ta": "self",
        "mt": "passive",
        "v": "",
        "ms": "",
        "st": 0,
        "g": "",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": [],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    },
    # 核心霸体视觉光环修饰器 (内置默认)：TuningGameplay 默认挂载，监听 onTypeActivate (type=unstoppable) 自动播放光环
    "gb_unstoppfx": {
        "id": "gb_unstoppfx",
        "t": "play_move",
        "tm": "status_unstoppable",
        "tr": ["onTypeActivate"],
        "uit": [],
        "pri": 0,
        "trm": 0.0,
        "trs": "type=unstoppable",
        "trr": "repeat",
        "c": 1.0,
        "m": 1.0,
        "d": -1.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 0,
        "g": "",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": [],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    },
    # 核心霸体视觉光环移除器 (内置默认)：TuningGameplay 默认挂载，监听 onTypeExpiry (type=unstoppable) 自动移除光环
    "gb_unstoppfxrmv": {
        "id": "gb_unstoppfxrmv",
        "t": "remove",
        "tm": "gb_unstoppfx",
        "tr": ["onTypeExpiry"],
        "uit": [],
        "pri": 0,
        "trm": 0.0,
        "trs": "type=unstoppable",
        "trr": "repeat",
        "c": 1.0,
        "m": 1.0,
        "d": 0.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 0,
        "g": "",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": [],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    },
}


def build_stat_mods():
    """汇总全局系统底层修饰器、全员 SP 技能呼出修饰器与各机器人专属能力修饰器、英雄招牌与 UI 展示能力。"""
    # 0. 核心底层系统修饰器 (受创硬直 gp_hit_stun、跳字累加器 gp_dmg_ft/gp_heal_ft)
    mods = dict(SYSTEM_GLOBAL_STATMODS)

    # 1. 78 位英雄 SP 呼出修饰器
    mods.update(build_sp_callout_statmods())

    # 2. 各机器人注册的修饰器
    bot_mods, _, _ = collect_all_bot_statmods_and_appears()
    mods.update(bot_mods)

    # 3. 官方英雄招牌技能与 UI 基础能力
    try:
        from .. import character_profiles
    except Exception:
        import character_profiles
    mods.update(character_profiles.get_profile_stat_modifiers())

    return mods


# 兼容 gamedata 调用的别名
build_stat_modifiers = build_stat_mods


def bot_abilities(bot_id: str):
    """查询指定金刚拥有的全部能力修饰器 ID 列表（包含通用 SP 技名呼出、UI 展示基础能力与专属技能）。"""
    sp_mods = [f"sp_callout_{bot_id}_{lvl}" for lvl in (1, 2, 3)] if bot_id in BOT_SP_MAP else []
    bot_custom_mods = get_bot_mod_ids(bot_id)
    try:
        from .. import character_profiles
    except Exception:
        import character_profiles
    ui_mods = character_profiles.get_bot_ui_ability_ids(bot_id)
    return ["gp_evade_callout"] + sp_mods + bot_custom_mods + ui_mods
