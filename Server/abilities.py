#!/usr/bin/env python3
"""
TFTF Combat Ability & Buff System (战斗能力与 Buff 系统配置模块)
================================================================

本模块为 Transformers Forged To Fight 离线版战斗能力系统的【独立单一真理源】。
负责定义：
  1. 全局 Buff 行为定义 (buffs_set / globalBuffs)
  2. UI 分组与堆叠策略 (buffs_config / groupings)
  3. 技能外观表现与 PUA 字体图标 (statModAppears)
  4. 战斗修饰器与触发逻辑 (statMods)
  5. 角色与技能的绑定关系 (bot_abilities)

----------------------------------------------------------------
【底层 IL2CPP 契约与逆向铁律 (必读)】：
  1. 数值 m (Magnitude) 是持续时间 d 内的【绝对总伤害数值】，绝非攻击力百分比！
     - 伤害 Tick 公式：per_tick = m / (d * 2.0) （每 0.5s Tick 一次，总共 2*d 次）
     - 因客户端跳字强转整型 int，若 m <= 2*d 会截断为 0，导致静默无伤害无跳字。
  2. 颜色代码 (tc, gt, gb) 必须使用【纯 6 位十六进制字符串】（如 "FF0000"），严禁加 "#"！
     - 底层 HexToColor (0x18AF58C) 从 index 0 开始两两读取，"#" 会被 0x18AB274 解析为 0xF，
       导致 "#FF0000" 移位错位解析为 RGB(255, 240, 0) 亮黄色！
  3. 列表访问器类型安全：tr、uit、a 字段在底层均为 C# List，必须传入 Python 数组 (如 ["onHit"])。
  4. PUA 字体图标：Tecnica_Bold_116.ttf 矢量字体，\uE401 为流血能量块滴液图标。
----------------------------------------------------------------
"""

import os

# ---------------------------------------------------------------------------
# 1. Buff UI 分组与显示配置 (buffs_config)
# ---------------------------------------------------------------------------
def build_buffs_config():
    """定义战斗中各类 Buff 的堆叠与血条下 UI 挂件显示策略。"""
    groups_data = {
        # 跳字累加器：常驻不可见
        "floating_text": {"stackable": True, "active_display": False},
        "floating_text_dmg": {"stackable": True, "active_display": False},
        "floating_text_heal": {"stackable": True, "active_display": False},
        # 流血类 Debuff：可堆叠，在敌人血条下方显示倒计时圆环图标
        "dmg_bleed": {"stackable": True, "active_display": True},
        # 直接伤害：不显示血条下方图标
        "dmg_direct": {"stackable": True, "active_display": False},
    }
    return {
        # 客户端 BuffsConfig.<groups>k__BackingField 期望字段名为 groups
        "groups": groups_data,
        "groupings": groups_data,
    }


# ---------------------------------------------------------------------------
# 2. 全局 Buff 引擎行为 (buffs_set)
# ---------------------------------------------------------------------------
def build_buffs_set():
    """全局 Buff 模板库。每个 id 对应 Damage_BuffEffect 或 FloatingText_BuffEffect。"""
    return {
        "globalBuffs": {
            # 伤害跳字收集器：捕获 _ftd 变量累加值，弹出红色跳字 (style 7)
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
            # 治疗跳字收集器：捕获 _fth 变量累加值，弹出绿色跳字 (style 6)
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
            # 阿尔茜普通爆头即时直接伤害 (Direct instant damage)
            "dmg_direct": {
                "id": "dmg_direct",
                "iconTexture": "",
                "image": "",
                "images3": False,
                "modeAvail": [],
                "scope": "global",
                "valueType": "absolute",
                "displayValue": 2091.0,
                "c": 1,
                "value": 2091.0,
                "buffType": "damage",
                "group": "dmg_direct",
                "p": {"damage_type": "bleed"},
                "hasDuration": True,
                "e": 0,
                "time": {"amount": 0.5},
                "loc_name": "headshot_direct",
                "loc_desc": "headshot_direct",
            },
            # 阿尔茜爆头流血 3 秒 DOT (3.0s Bleed DOT)
            "dmg_bleed": {
                "id": "dmg_bleed",
                "iconTexture": "",
                "image": "",
                "images3": False,
                "modeAvail": [],
                "scope": "global",
                "valueType": "absolute",
                "displayValue": 2091.0,
                "c": 1,
                "value": 2091.0,
                "buffType": "damage",
                "group": "dmg_bleed",
                "p": {"damage_type": "bleed"},
                "hasDuration": True,
                "e": 0,
                "time": {"amount": 3.0},
                "loc_name": "bleed",
                "loc_desc": "bleed",
            },
            # 阿尔茜 S2 暴击流血 4 秒 DOT (4.0s Bleed DOT)
            "dmg_bleed_s2": {
                "id": "dmg_bleed_s2",
                "iconTexture": "",
                "image": "",
                "images3": False,
                "modeAvail": [],
                "scope": "global",
                "valueType": "absolute",
                "displayValue": 3764.0,
                "c": 1,
                "value": 3764.0,
                "buffType": "damage",
                "group": "dmg_bleed",
                "p": {"damage_type": "bleed"},
                "hasDuration": True,
                "e": 0,
                "time": {"amount": 4.0},
                "loc_name": "bleed",
                "loc_desc": "bleed",
            },
        },
        "userBuffs": {}
    }


# ---------------------------------------------------------------------------
# 3. 视觉表现与图标映射 (statModAppears)
# ---------------------------------------------------------------------------
def build_stat_mod_appears():
    """定义修饰器的视觉效果、Unicode PUA 图标字形、呼出文字及纯 6 位 Hex 颜色。"""
    return {
        # 阿尔茜爆头即时直接命中外观
        "appr_arcee_headshot": {
            "id": "appr_arcee_headshot",
            "a": "Headshot",
            "s": "Headshot",
            "l": "Direct headshot strike inflicts extra direct damage.",
            "ss": "Direct headshot damage.",
            "t": "\uE401",                # 能量块流血字形
            "f": "",
            "st": "HEADSHOT",             # 命中呼出大字
            "ps": "Headshot",
            "pl": "Direct headshot damage.",
            "tc": "FF0000",               # 纯 6 位 Hex：鲜红色 (严禁带 '#')
            "gt": "FF0000",
            "gb": "FF0000",
        },
        # 阿尔茜流血 DOT 持续伤害外观
        "appr_arcee_bleed": {
            "id": "appr_arcee_bleed",
            "a": "Bleed",
            "s": "Bleed",
            "l": "Direct bleed damage ignoring armor over duration.",
            "ss": "Bleed damage over duration.",
            "t": "\uE401",                # 能量块流血字形（血条下方倒计时圆环图标）
            "f": "",
            "st": "BLEED",                # 呼出大字
            "ps": "Bleed",
            "pl": "Bleed damage ignoring armor.",
            "tc": "FF0000",               # 纯正红色 (0xFF, 0x00, 0x00)
            "gt": "FF0000",
            "gb": "FF0000",
        },
    }


# ---------------------------------------------------------------------------
# 4. 战斗修饰器与触发器定义 (statMods)
# ---------------------------------------------------------------------------
def build_stat_modifiers():
    """定义具体的触发条件、几率、持续时间与作用对象。"""
    return {
        # -------------------------------------------------------------------
        # [全局系统修饰器]
        # -------------------------------------------------------------------
        # 受击硬直修饰器 (内置默认)
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

        # -------------------------------------------------------------------
        # [阿尔茜 Arcee 官方技能组]
        # 基准属性（R5 L50）：攻击力 3485，暴击率 32%，暴击伤害 1.70x
        # -------------------------------------------------------------------
        # 1. 爆头射击 (Headshot) - 远程暴击额外直接扣血 60% 攻击力 (2091点)
        #    触发条件：普通远程射击 (onRangedHit) 或 特殊技1/3子弹 (onSpecial1Hit, onSpecial3Hit)
        #    基础几率：50% (c: 0.5)
        "arcee_headshot_direct": {
            "id": "arcee_headshot_direct",
            "t": "dmg_direct",
            "tm": "",
            "tr": ["onRangedHit", "onSpecial1Hit", "onSpecial3Hit"],
            "uit": ["onRangedHit", "onSpecial1Hit", "onSpecial3Hit"],
            "pri": 0,
            "trm": 0.0,
            "trs": "",
            "trr": "repeat",
            "c": 0.5,                    # 基础 50% 触发几率
            "m": 2091.0,                 # 60% 攻击力 (3485 * 0.6 = 2091 点直接伤害)
            "d": 0.5,                    # 单 Tick 结算即时扣除
            "s": "none",
            "ta": "opponent",            # 作用于对手
            "mt": "debuff",
            "v": "",
            "ms": "",
            "st": 1,
            "g": "",
            "gc": 0.0,
            "gcv": "",
            "rcv": "",
            "ti": 0,
            "a": ["appr_arcee_headshot"],# 弹出 "HEADSHOT" 红色大字
            "au": [],
            "rh": 0.0,
            "ra": 0.0,
        },

        # 2. 爆头流血 (Headshot Bleed) - 远程暴击施加 3 秒流血 DOT
        #    总伤害：60% 攻击力 (2091点)，3秒内每0.5秒一跳 (每跳 348点)
        #    基础几率：50% (c: 0.5)
        "arcee_headshot_dot": {
            "id": "arcee_headshot_dot",
            "t": "dmg_bleed",
            "tm": "",
            "tr": ["onRangedHit", "onSpecial1Hit", "onSpecial3Hit"],
            "uit": ["onRangedHit", "onSpecial1Hit", "onSpecial3Hit"],
            "pri": 0,
            "trm": 0.0,
            "trs": "",
            "trr": "repeat",
            "c": 0.5,                    # 基础 50% 几率
            "m": 2091.0,                 # 3秒总伤害 2091 点 (每跳 348 伤害)
            "d": 3.0,                    # 持续 3 秒
            "s": "none",
            "ta": "opponent",
            "mt": "debuff",              # 敌方血条下方生成倒计时圆环图标
            "v": "",
            "ms": "",
            "st": 1,
            "g": "",
            "gc": 0.0,
            "gcv": "",
            "rcv": "",
            "ti": 0,
            "a": ["appr_arcee_bleed"],   # 关联能量块滴液流血图标与 "BLEED"
            "au": [],
            "rh": 0.0,
            "ra": 0.0,
        },

        # 3. 爆头冲锋惩罚 (Headshot Rush) - 敌人冲刺 (Dashing) 中枪时 100% 必出流血
        #    额外 50% 几率补足（与基础 50% 叠加达成 100%）
        "arcee_headshot_rush": {
            "id": "arcee_headshot_rush",
            "t": "dmg_bleed",
            "tm": "",
            "tr": ["onRangedHit", "onSpecial1Hit", "onSpecial3Hit"],
            "uit": ["onRangedHit", "onSpecial1Hit", "onSpecial3Hit"],
            "pri": 0,
            "trm": 0.0,
            "trs": "opponent:state=Dashing", # 敌人冲锋状态判定
            "trr": "repeat",
            "c": 0.5,                    # 额外 50% 几率（叠加为 100%）
            "m": 2091.0,
            "d": 3.0,
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
            "a": ["appr_arcee_bleed"],
            "au": [],
            "rh": 0.0,
            "ra": 0.0,
        },

        # 4. S2 暴击流血 (Special Attack 2 Bleed)
        #    触发条件：S2 命中 (onSpecial2Hit)
        #    几率：100% (c: 1.0)
        #    总伤害：108% 攻击力 (3485 * 1.08 = 3764 点)，持续 4 秒 (每跳 470 点)
        "arcee_s2_bleed": {
            "id": "arcee_s2_bleed",
            "t": "dmg_bleed_s2",
            "tm": "",
            "tr": ["onSpecial2Hit"],
            "uit": ["onSpecial2Hit"],
            "pri": 0,
            "trm": 0.0,
            "trs": "",
            "trr": "repeat",
            "c": 1.0,                    # 100% 触发几率
            "m": 3764.0,                 # 108% 攻击力 (4秒总伤害 3764 点，每跳 470 伤害)
            "d": 4.0,                    # 持续 4 秒
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
            "a": ["appr_arcee_bleed"],
            "au": [],
            "rh": 0.0,
            "ra": 0.0,
        },
    }


# ---------------------------------------------------------------------------
# 5. 角色与技能绑定表 (bot_abilities)
# ---------------------------------------------------------------------------
BOT_ABILITIES_MAP = {
    # 阿尔茜：配置爆头直接扣血、爆头3秒流血、冲锋100%流血强化、以及S2暴击流血
    "arcee_gs_deluxe2014": [
        "arcee_headshot_direct",
        "arcee_headshot_dot",
        "arcee_headshot_rush",
        "arcee_s2_bleed",
    ],
}


def bot_abilities(bot_id):
    """查询指定金刚拥有的全部能力修饰器 ID 列表。"""
    return BOT_ABILITIES_MAP.get(bot_id, [])
