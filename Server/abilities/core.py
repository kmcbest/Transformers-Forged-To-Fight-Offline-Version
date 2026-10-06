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
            
    # 3. 数值截断防护：仅对流血/DOT伤害修饰器检测单次 Tick 伤害
    t = str(mod.get("t", ""))
    d = float(mod.get("d", 0.0))
    m = float(mod.get("m", 0.0))
    if t.startswith("dmg_") and d > 0 and m > 0:
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
    callout_text: str = "流血",
    is_zh: bool = True,
    stackable: bool = True,
    buff_id: str = "dmg_bleed",
    target_scope: str = "none",
    target_actor: str = "opponent",
    pua_icon: str = "\uE401",
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
    :param callout_text: 触发呼出文字 (优先使用中文，如 '流血' / '爆头')
    """
    validate_color_code("FF0000", "bleed_tc")

    appear = {
        "id": appr_id,
        "a": callout_text,
        "s": "",                      # ShortStringID 为空，防止被当作角色常驻被动能力列表项
        "l": f"{callout_text}持续伤害",
        "ss": f"{callout_text}持续伤害",
        "t": pua_icon,                # 能量块流血字形（血条下方倒计时圆环图标）
        "f": "",
        "st": callout_text,           # 命中呼出大字 (如 流血 / 爆头)
        "ps": callout_text,
        "pl": f"{callout_text}生效中",
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


def make_unstoppable_statmod(
    mod_id: str,
    duration: float,
    trigger: str = "onSpecial2Activate",
    trigger_scope: str = "",
    appr_id: str = "appr_unstoppable",
    callout_text: str = "不可阻挡",
    show_callout: bool = True,
    play_vfx: bool = False,
    vfx_move: str = "status_unstoppable",
    pua_icon: str = "\uE915",
    color_hex: str = "FFAA00",
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    通用不可阻挡 (Unstoppable / 霸体) 工厂：
    1. 赋予 'unstoppable' BuffEffect，直接提升底层属性 _unstoppable，
       使 PlayerController.ReceiveHit 彻底跳过 ApplyHitStun，实现受创不打断动作，
       同时正常扣除伤害并缩放击退。
    2. 若 play_vfx 为 True，附带 'play_move' 播放角色周身金色霸体光环与粒子特效 (status_unstoppable)。
    3. 若 show_callout 为 True，弹出金色 "不可阻挡" 命中呼出大字与 PUA 矢量图标。
    """
    validate_color_code(color_hex, "unstoppable_color")

    appear = {
        "id": appr_id,
        "a": callout_text,
        "s": "",                      # 留空，避免被误判为常规被动展示项
        "l": "受到攻击不会产生硬直",
        "ss": "受到攻击不会产生硬直",
        "t": pua_icon,                # PUA 矢量图标：不可阻挡 (\uE915)
        "f": "",
        "st": callout_text if show_callout else "",
        "ps": callout_text,
        "pl": "不可阻挡生效中",
        "tc": color_hex,
        "gt": color_hex,
        "gb": "FF8800",
    }

    stat_mod = {
        "id": mod_id,
        "t": "unstoppable",
        "tm": "",
        "tr": [trigger],
        "uit": [trigger] if show_callout else [],
        "pri": 0,
        "trm": 0.0,
        "trs": trigger_scope,
        "trr": "repeat",
        "c": 1.0,
        "m": 1.0,
        "d": float(duration),
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": [appr_id] if show_callout else [],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }

    validate_statmod(stat_mod)
    validate_appear(appear)

    mods = {mod_id: stat_mod}
    appears = {appr_id: appear} if show_callout else {}

    if play_vfx:
        vfx_mod_id = f"{mod_id}_vfx"
        vfx_mod = {
            "id": vfx_mod_id,
            "t": "play_move",
            "tm": vfx_move,
            "tr": [trigger],
            "uit": [],
            "pri": 0,
            "trm": 0.0,
            "trs": trigger_scope,
            "trr": "repeat",
            "c": 1.0,
            "m": 1.0,
            "d": float(duration),
            "s": "none",
            "ta": "self",
            "mt": "buff",
            "v": "",
            "ms": "",
            "st": 1,
            "g": "",
            "gc": 0.0,
            "gcv": "",
            "rcv": "",
            "ti": 0,
            "a": [],
            "au": [],
            "rh": 0.0,
            "ra": 0.0,
        }
        validate_statmod(vfx_mod)
        mods[vfx_mod_id] = vfx_mod

    return mods, appears


def make_ranged_boost_statmod(
    mod_id: str,
    duration: float,
    damage_bonus: float = 0.0,
    speed_bonus: float = 0.0,
    trigger: str = "onSpecial1Activate",
    trigger_scope: str = "",
    appr_id: str = "appr_ranged_boost",
    callout_text: str = "远程增益",
    show_callout: bool = True,
    pua_icon: str = "\uE41B",
    color_hex: str = "FFAA00",
    gradient_bottom: str = "FF6600",
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    通用远程增益工厂 (Ranged Boost Buff):
    支持伤害加成 (damage_bonus)、射速/弹速加成 (speed_bonus) 与持续时间 (duration) 独立解耦配置。
    - 阿尔茜 SP1: damage_bonus=0.35, speed_bonus=0.20, duration=6.5 (加伤又提速)
    - 幻影 招牌: damage_bonus=0.0, speed_bonus=0.25, duration=8.0 (只提速不加伤)
    正向增益，归属 'ranged_buff' 组，可被敌人 Nullify 驱散。
    外观颜色为标准正面增益暖橙色 (FFAA00 / FF6600)。
    """
    validate_color_code(color_hex, "ranged_boost_tc")
    validate_color_code(gradient_bottom, "ranged_boost_gb")

    appear = {
        "id": appr_id,
        "a": callout_text,
        "s": "",                      # 留空防被当作常驻被动列表项
        "l": "提升远程攻击作战属性",
        "ss": "提升远程攻击作战属性",
        "t": pua_icon,                # PUA 矢量图标: 飞射弹头 (\uE41B)
        "f": "",
        "st": callout_text if show_callout else "",
        "ps": callout_text,
        "pl": f"{callout_text}生效中",
        "tc": color_hex,
        "gt": color_hex,
        "gb": gradient_bottom,
    }

    stat_mod = {
        "id": mod_id,
        "t": "ranged_buff",
        "tm": "",
        "tr": [trigger],
        "uit": [trigger] if show_callout else [],
        "pri": 0,
        "trm": 0.0,
        "trs": trigger_scope,
        "trr": "repeat",
        "c": 1.0,
        "m": float(damage_bonus),     # 伤害增益幅度 (如 0.35)
        "d": float(duration),         # 持续时间 (秒)
        "s": "none",
        "ta": "self",                 # 作用于自身
        "mt": "buff",                 # 正向增益 (可被驱散)
        "v": "",
        "ms": "",
        "st": 1,
        "g": "ranged_buff",           # 增益类别组: ranged_buff
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": [appr_id] if show_callout else [],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
        # 扩展属性负载：若带提速，存入 params 供客户端或 Hook 解析
        "speed_bonus": float(speed_bonus),
    }

    validate_statmod(stat_mod)
    validate_appear(appear)
    return {mod_id: stat_mod}, {appr_id: appear}


def make_shock_statmod(
    mod_id: str,
    duration: float,
    total_dmg: float,
    chance: float = 1.0,
    trigger: str = "onHit",
    trigger_scope: str = "",
    appr_id: str = "appr_shock",
    callout_text: str = "震击",
    is_zh: bool = True,
    stackable: bool = True,
    target_scope: str = "none",
    target_actor: str = "opponent",
    pua_icon: str = "\uE914",
    color_hex: str = "FF0000",
    gradient_bottom: str = "FF0000",
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    通用震击 DOT 工厂 (Shock DOT):
    造成持续能量伤害 (Energy Damage over time)。
    - 绑定至 buffs_set 中的 dmg_shock。
    - PUA 图标为雷电 (\uE914)，配色为减益红色 (FF0000 / FF0000)。
    """
    validate_color_code(color_hex, "shock_tc")
    validate_color_code(gradient_bottom, "shock_gb")

    appear = {
        "id": appr_id,
        "a": callout_text,
        "s": "",
        "l": "持续造成能量伤害",
        "ss": "持续造成能量伤害",
        "t": pua_icon,
        "f": "",
        "st": callout_text,
        "ps": callout_text,
        "pl": f"{callout_text}生效中",
        "tc": color_hex,
        "gt": color_hex,
        "gb": gradient_bottom,
    }

    stat_mod = {
        "id": mod_id,
        "t": "dmg_shock",
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
        "s": target_scope,
        "ta": target_actor,
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 10 if stackable else 1,
        "g": "shock_debuff",
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


def make_power_leak_statmod(
    mod_id: str,
    duration: float,
    drain_bars: float = 0.40,
    chance: float = 1.0,
    trigger: str = "onHit",
    trigger_scope: str = "",
    appr_id: str = "appr_power_leak",
    callout_text: str = "能量流失",
    pua_icon: str = "\uE607",
    color_hex: str = "FF0000",
    gradient_bottom: str = "FF0000",
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    通用能量流失工厂 (Power Leak Debuff):
    在指定持续时间内持续扣除对手能量条 (Substracts power over duration)。
    - PUA 图标为能量漏斗 (\uE607)，配色为减益红色 (FF0000 / FF0000)。
    """
    validate_color_code(color_hex, "power_leak_tc")
    validate_color_code(gradient_bottom, "power_leak_gb")

    appear = {
        "id": appr_id,
        "a": callout_text,
        "s": "",
        "l": "持续扣除对手能量条",
        "ss": "持续扣除对手能量条",
        "t": pua_icon,
        "f": "",
        "st": callout_text,
        "ps": callout_text,
        "pl": f"{callout_text}生效中",
        "tc": color_hex,
        "gt": color_hex,
        "gb": gradient_bottom,
    }

    stat_mod = {
        "id": mod_id,
        "t": "power_leak",
        "tm": "",
        "tr": [trigger],
        "uit": [trigger],
        "pri": 0,
        "trm": 0.0,
        "trs": trigger_scope,
        "trr": "repeat",
        "c": float(chance),
        "m": float(drain_bars),       # 扣除格数 (如 0.40 表示扣除一格的40%)
        "d": float(duration),
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 5,
        "g": "power_leak_debuff",
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


def make_stun_statmod(
    mod_id: str,
    duration: float,
    chance: float = 1.0,
    trigger: str = "onSpecial1Activate",
    trigger_scope: str = "",
    appr_id: str = "appr_stun",
    callout_text: str = "眩晕",
    pua_icon: str = "\uE605",
    color_hex: str = "FFE000",
    gradient_bottom: str = "FFAA00",
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    通用眩晕硬控工厂 (Stun Debuff):
    击晕目标，使其在持续时间内无法行动与攻击。
    - PUA 图标为眩晕星星 (\uE605)，配色为亮黄/金黄 (FFE000 / FFAA00)。
    """
    validate_color_code(color_hex, "stun_tc")
    validate_color_code(gradient_bottom, "stun_gb")

    appear = {
        "id": appr_id,
        "a": callout_text,
        "s": "",
        "l": "目标陷入眩晕，无法行动",
        "ss": "目标陷入眩晕，无法行动",
        "t": pua_icon,
        "f": "",
        "st": callout_text,
        "ps": callout_text,
        "pl": f"{callout_text}生效中",
        "tc": color_hex,
        "gt": color_hex,
        "gb": gradient_bottom,
    }

    stat_mod = {
        "id": mod_id,
        "t": "stun",
        "tm": "",
        "tr": [trigger],
        "uit": [trigger],
        "pri": 0,
        "trm": 0.0,
        "trs": trigger_scope,
        "trr": "repeat",
        "c": float(chance),
        "m": 1.0,
        "d": float(duration),
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 1,                      # 眩晕不可重复堆叠，仅刷新时长
        "g": "stun_debuff",
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


def make_nullify_statmod(
    mod_id: str,
    target_categories: Optional[List[str]] = None,
    max_stacks_per_cat: int = 1,
    chance: float = 1.0,
    trigger: str = "onHit",
    trigger_scope: str = "level=Special1",
    appr_id: str = "appr_nullify",
    callout_text: str = "驱散",
    pua_icon: str = "\uE950",
    color_hex: str = "38BDF8",
    gradient_bottom: str = "0284C7",
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    通用驱散工厂 (Nullify / Dispel):
    驱散/移除目标身上指定类别的正面增益 Buff (近战、远程、特技增益等)。
    - PUA 图标为碎裂驱散 (\uE950)，配色为天蓝 (38BDF8 / 0284C7)。
    """
    if target_categories is None:
        target_categories = ["melee", "ranged", "special"]

    validate_color_code(color_hex, "nullify_tc")
    validate_color_code(gradient_bottom, "nullify_gb")

    appear = {
        "id": appr_id,
        "a": callout_text,
        "s": "",
        "l": "驱散目标正面增益",
        "ss": "驱散目标正面增益",
        "t": pua_icon,
        "f": "",
        "st": callout_text,
        "ps": callout_text,
        "pl": f"{callout_text}生效中",
        "tc": color_hex,
        "gt": color_hex,
        "gb": gradient_bottom,
    }

    stat_mod = {
        "id": mod_id,
        "t": "nullify",
        "tm": "",
        "tr": [trigger],
        "uit": [trigger],
        "pri": 0,
        "trm": 0.0,
        "trs": trigger_scope,
        "trr": "repeat",
        "c": float(chance),
        "m": float(max_stacks_per_cat),
        "d": 0.5,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 0,
        "g": "nullify_debuff",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": [appr_id],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
        "target_categories": target_categories,
    }

    validate_statmod(stat_mod)
    validate_appear(appear)
    return {mod_id: stat_mod}, {appr_id: appear}



