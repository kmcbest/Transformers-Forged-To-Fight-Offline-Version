#!/usr/bin/env python3
"""
TFTF Combat Ability Core Engine & Mechanic Templates
===================================================
战斗能力系统的中层核心库与通用机制工厂。
负责：
  1. 封装符合底层 IL2CPP 契约的标准 StatMod / StatModAppear 工厂函数；
  2. 统一定义流血 (Bleed)、直伤 (Direct Damage)、破甲 (Armor Break)、感电 (Shock) 等机制模板；
  3. 执行严格的底层契约与类型安全校验（颜色纯6位十六进制、数值截断防护、列表包装等）。
"""

from typing import Dict, Any, Tuple, List, Optional


# ---------------------------------------------------------------------------
# 1. 契约校验器 (Contract Validators)
# ---------------------------------------------------------------------------

def validate_color_code(color: str, field_name: str = "color"):
    """校验颜色字符串：必须为纯 6 位十六进制，严禁带 '#'。"""
    if not isinstance(color, str):
        raise ValueError(f"[{field_name}] 必须为字符串: {color}")
    if color.startswith("#"):
        raise ValueError(f"[{field_name}] 严禁带 '#' 前缀，请使用纯 6 位十六进制代码: '{color}' -> '{color.lstrip('#')}'")
    if len(color) != 6:
        raise ValueError(f"[{field_name}] 长度必须恰好为 6 位十六进制: '{color}'")
    int(color, 16)  # 验证是否为合法十六进制


def validate_statmod(mod: Dict[str, Any]):
    """校验 StatMod 字典是否完全符合客户端底层反编译契约。"""
    mod_id = mod.get("id", "unknown")
    # 1. 必须有 id 与 t
    if not mod.get("id") or not mod.get("t"):
        raise ValueError(f"StatMod [{mod_id}] 缺少必需的 'id' 或 't' (类型)")
    
    # 2. tr, uit, a, au 必须为列表
    for list_field in ("tr", "uit", "a", "au"):
        val = mod.get(list_field)
        if val is not None and not isinstance(val, (list, tuple)):
            raise TypeError(f"StatMod [{mod_id}] 字段 '{list_field}' 必须为 List/Tuple，得到: {type(val)}")
            
    # 3. 数值截断防护：如果具有持续时间 d 且伤害总量 m > 0
    d = float(mod.get("d", 0.0))
    m = float(mod.get("m", 0.0))
    if d > 0 and m > 0:
        ticks = d * 2.0  # 游戏每 0.5 秒结算一次
        if m / ticks < 1.0:
            print(f"[WARN][Ability Contract] StatMod [{mod_id}] 伤害数值 m={m} 在 d={d}s 下单次 Tick 伤害为 {m/ticks:.2f} < 1.0，客户端将强转截断为 0！")


def validate_appear(appr: Dict[str, Any]):
    """校验 StatModAppear 字典。"""
    appr_id = appr.get("id", "unknown")
    for c_field in ("tc", "gt", "gb", "bc"):
        if c_field in appr and appr[c_field]:
            validate_color_code(appr[c_field], f"{appr_id}.{c_field}")


# ---------------------------------------------------------------------------
# 2. 通用机制工厂函数 (Mechanic Factories)
# ---------------------------------------------------------------------------

def make_bleed_statmod(
    mod_id: str,
    duration: float,
    total_dmg: float,
    chance: float = 1.0,
    trigger: str = "onCrit",
    trigger_scope: str = "",
    appr_id: str = "appr_bleed",
    callout_text: str = "BLEED",
    is_zh: bool = True,
    stackable: bool = True,
    buff_id: str = "dmg_bleed",
    target_scope: str = "none",
    target_actor: str = "opponent",
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    通用流血 (Bleed DOT) 工厂：
    返回 (stat_mods_dict, stat_mod_appears_dict)
    
    :param mod_id: 修饰器唯一 ID (如 "arcee_headshot_dot", "windblade_crit_bleed")
    :param duration: 持续时间 (秒)
    :param total_dmg: 持续时间内的总伤害绝对数值 (m)
    :param chance: 触发概率 (0.0 ~ 1.0)
    :param trigger: 触发时机 ("onCrit", "onHit", "onSpecial1Activate" 等)
    :param trigger_scope: 触发范围 ("level=Ranged", "level=Special2" 等)
    :param appr_id: 外观表现 ID
    :param callout_text: 触发呼出文字
    """
    validate_color_code("FF0000", "bleed_tc")

    appear = {
        "id": appr_id,
        "a": callout_text.capitalize(),
        "s": callout_text.capitalize(),
        "l": f"{callout_text.capitalize()} damage over duration.",
        "ss": f"{callout_text.capitalize()} damage over duration.",
        "t": "\uE401",                # 能量块流血字形（血条下方倒计时圆环图标）
        "f": "",
        "st": callout_text,           # 命中呼出大字 (如 BLEED / HEADSHOT)
        "ps": callout_text.capitalize(),
        "pl": f"{callout_text.capitalize()} damage ignoring armor.",
        "tc": "FF0000",               # 纯 6 位 Hex：鲜红色 (严禁带 '#')
        "gt": "FF0000",
        "gb": "FF0000",
    }

    stat_mod = {
        "id": mod_id,
        "t": buff_id,        # 绑定至 buffs_set 中的 dmg_bleed
        "tm": "",
        "tr": [trigger],
        "uit": [trigger],
        "pri": 0,
        "trm": 0.0,
        "trs": trigger_scope,
        "trr": "repeat",
        "c": float(chance),
        "m": float(total_dmg),
        "d": float(duration),
        "s": target_scope,   # 作用范围 ("none")
        "ta": target_actor,  # 作用目标 ("opponent")
        "mt": "debuff",      # 负面效果
        "v": "",
        "ms": "",
        "st": 10 if stackable else 1,  # 堆叠层数
        "g": "",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": [appr_id],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }

    validate_statmod(stat_mod)
    validate_appear(appear)

    return {mod_id: stat_mod}, {appr_id: appear}


def make_direct_dmg_statmod(
    mod_id: str,
    dmg: float,
    chance: float = 1.0,
    trigger: str = "onCrit",
    trigger_scope: str = "",
    buff_id: str = "dmg_direct",
    target_scope: str = "none",
    target_actor: str = "opponent",
    mod_type: str = "passive",
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    通用即时额外直接伤害 (Direct Damage) 工厂：
    无独立 Callout Text 表现，直接触发扣血跳字。
    """
    stat_mod = {
        "id": mod_id,
        "t": buff_id,
        "tm": "",
        "tr": [trigger],
        "uit": [trigger],
        "pri": 0,
        "trm": 0.0,
        "trs": trigger_scope,
        "trr": "repeat",
        "c": float(chance),
        "m": float(dmg),
        "d": 0.5,            # 短持续时间
        "s": target_scope,
        "ta": target_actor,
        "mt": mod_type,
        "v": "",
        "ms": "",
        "st": 0,
        "g": "",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": [],             # 直伤无图标呼出
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(stat_mod)
    return {mod_id: stat_mod}, {}

