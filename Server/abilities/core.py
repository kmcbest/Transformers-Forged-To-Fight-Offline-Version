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
    - 底层对接官方原生 'power_gain' BuffEffect 并传入负数值。
    - 官方基准 1 格能量 = 300 点 Mana (3格满气共 900 点)。
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

    # 官方 1 格能量基准为 300 点 Mana
    total_drain_mana = -300.0 * float(drain_bars)

    stat_mod = {
        "id": mod_id,
        "t": "power_gain",
        "tm": "",
        "tr": [trigger],
        "uit": [trigger],
        "pri": 0,
        "trm": 0.0,
        "trs": trigger_scope,
        "trr": "repeat",
        "c": float(chance),
        "m": float(total_drain_mana),       # 传入负数 Mana，由官方原生 PowerGain_BuffEffect 持续扣除
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
    target_actor: str = "opponent",
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
        "ta": target_actor,
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


def make_evade_grant_statmod(
    mod_id: str,
    evade_type: str = "melee",          # "melee" or "ranged"
    grant_chance: float = 1.0,          # 获得此 Buff 的概率 (例如后闪 1.0，被击倒 0.85)
    evade_chance: float = 1.0,          # 触发规避的概率 (例如小黄蜂 0.32，路障 1.0)
    duration: float = 3.0,              # >0 为倒计时型; <=0 为消耗型 (无倒计时，血条下方常驻)
    trigger: str = "onPlayerStateEnter",# 获得触发事件
    trigger_scope: str = "state=Dodge", # 获得触发条件范围
    appr_id: str = "",
    callout_text: str = "",             # "近战规避" 或 "远程规避"
    pua_icon: str = "",
    color_hex: str = "10B981",          # 纯6位十六进制绿色 (严禁带 '#')
    gradient_bottom: str = "059669",
    show_callout: bool = False,         # 获得时通常不弹字 (触发规避免伤时再呼出“规避”)
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    规避获得修饰器工厂 (Evade Grant StatMod Factory):
    - 明确区分两层概率：
      1. grant_chance: 角色采取特定行动或遭遇特定事件时，获得规避 Buff 的概率 (写入 'c')；
      2. evade_chance: 拥有该 Buff 后，受到攻击时真正成功躲避免伤的概率 (写入 'm')。
    - 图标显示为绿色圆环 (Buff)，PUA 图标：近战规避 0xe509 (\uE509)，远程规避 0xe518 (\uE518)；
    - 分倒计时型 (duration > 0) 与消耗型 (duration <= 0, 无倒计时, 触发规避后消耗)。
    """
    if not appr_id:
        appr_id = f"appr_{mod_id}"

    is_melee = (evade_type.lower() == "melee")
    if not callout_text:
        callout_text = "近战规避" if is_melee else "远程规避"
    if not pua_icon:
        pua_icon = "\uE509" if is_melee else "\uE518"

    validate_color_code(color_hex, "evade_tc")
    validate_color_code(gradient_bottom, "evade_gb")

    buff_type = "evade_melee" if is_melee else "evade_ranged"
    desc_text = "规避对手近战攻击并中断动作" if is_melee else "规避对手远程攻击并中断动作"

    appear = {
        "id": appr_id,
        "a": callout_text,
        "s": "",                      # 留空，避免被误判为常规被动展示项
        "l": desc_text,
        "ss": desc_text,
        "t": pua_icon,                # PUA 矢量图标: 近战 0xe509 / 远程 0xe518
        "f": "",
        "st": callout_text if show_callout else "",
        "ps": callout_text,
        "pl": f"{callout_text}生效中",
        "tc": color_hex,
        "gt": color_hex,
        "gb": gradient_bottom,
    }

    # 倒计时型使用实际 duration，消耗型 (无倒计时) 设置 duration = -1.0 (常驻直至被触发消耗)
    eff_duration = float(duration) if duration > 0 else -1.0
    buff_template_id = buff_type

    stat_mod = {
        "id": mod_id,
        "t": buff_template_id,
        "tm": "",
        "tr": [trigger],
        "uit": [trigger],
        "pri": 0,
        "trm": 0.0,
        "trs": trigger_scope,
        "trr": "repeat",
        "c": float(grant_chance),     # 获得 Buff 的概率
        "m": float(evade_chance),     # 受击时触发规避的概率 (0.32 或 1.0)
        "d": eff_duration,
        "s": "none",
        "ta": "self",                 # 作用于自身
        "mt": "buff",                 # 正向增益
        "v": "",
        "ms": "",
        "st": 1,                      # 不堆叠层数
        "g": buff_type,               # 增益类别组: evade_melee 或 evade_ranged
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": [appr_id],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
        "consume_on_evade": (duration <= 0),
        "evade_type": "melee" if is_melee else "ranged",
    }

    validate_statmod(stat_mod)
    validate_appear(appear)
    return {mod_id: stat_mod}, {appr_id: appear}


def make_evade_consume_statmod(
    mod_id: str,
    target_mod_id: str,
    evade_type: str = "melee",
    callout_text: str = "规避",
    appr_id: str = "",
    pua_icon: str = "",
    color_hex: str = "10B981",
    gradient_bottom: str = "059669",
    show_callout: bool = True,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    规避成功消耗与弹字工厂 (Evade Consume StatMod Factory):
    - 真正进入规避动作状态时 (state=EvadeMelee / EvadeRanged)，
      原生调用 Remove_BuffEffect 精准移除 target_mod_id，并呼出绿色大字 '规避'！
    """
    is_melee = (evade_type.lower() == "melee")
    target_state = "EvadeMelee" if is_melee else "EvadeRanged"
    if not pua_icon:
        pua_icon = "\uE509" if is_melee else "\uE518"

    return make_remove_statmod(
        mod_id=mod_id,
        target_mod_id=target_mod_id,
        trigger="onPlayerStateEnter",
        trigger_scope=f"state={target_state}",
        callout_text=callout_text,
        appr_id=appr_id,
        pua_icon=pua_icon,
        color_hex=color_hex,
        gradient_bottom=gradient_bottom,
        show_callout=show_callout,
    )


def make_evade_statmod(
    mod_id: str,
    evade_type: str = "melee",
    duration: float = 3.0,
    chance: float = 1.0,
    trigger: str = "onPlayerStateEnter",
    trigger_scope: str = "state=Dodge",
    appr_id: str = "",
    callout_text: str = "",
    consume_on_trigger: bool = False,
    pua_icon: str = "",
    color_hex: str = "10B981",
    gradient_bottom: str = "059669",
    show_callout: bool = True,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """兼容旧接口的规避工厂封装"""
    return make_evade_grant_statmod(
        mod_id=mod_id,
        evade_type=evade_type,
        grant_chance=chance,
        evade_chance=1.0,
        duration=duration,
        trigger=trigger,
        trigger_scope=trigger_scope,
        appr_id=appr_id,
        callout_text=callout_text,
        pua_icon=pua_icon,
        color_hex=color_hex,
        gradient_bottom=gradient_bottom,
        show_callout=show_callout,
    )



def make_crit_rate_statmod(
    mod_id: str,
    duration: float = 7.5,
    crit_bonus: float = 0.30,
    chance: float = 1.0,
    trigger: str = "onPlayerStateEnter",
    trigger_scope: str = "state=Knockdown",
    appr_id: str = "",
    callout_text: str = "暴击几率",
    pua_icon: str = "\uE406",
    color_hex: str = "F59E0B",
    gradient_bottom: str = "D97706",
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    通用暴击几率增益工厂 (Crit Rate Boost Buff):
    在指定持续时间内提升自身暴击几率。
    - PUA 图标为暴击标志 (\uE406)，配色为金黄琥珀色 (F59E0B / D97706)。
    """
    if not appr_id:
        appr_id = f"appr_{mod_id}"

    validate_color_code(color_hex, "crit_rate_tc")
    validate_color_code(gradient_bottom, "crit_rate_gb")

    appear = {
        "id": appr_id,
        "a": callout_text,
        "s": "",
        "l": f"暴击几率提升{int(crit_bonus*100)}%",
        "ss": f"暴击几率提升{int(crit_bonus*100)}%",
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
        "t": "crit_rate",
        "tm": "",
        "tr": [trigger],
        "uit": [trigger],
        "pri": 0,
        "trm": 0.0,
        "trs": trigger_scope,
        "trr": "repeat",
        "c": float(chance),
        "m": float(crit_bonus),
        "d": float(duration),
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "crit_rate",
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


def make_crit_damage_statmod(
    mod_id: str,
    duration: float = 4.0,
    crit_dmg_bonus: float = 0.75,
    chance: float = 1.0,
    trigger: str = "onSpecial2Activate",
    trigger_scope: str = "",
    appr_id: str = "",
    callout_text: str = "暴击伤害",
    pua_icon: str = "\uE406",
    color_hex: str = "F59E0B",
    gradient_bottom: str = "D97706",
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    通用暴击伤害增益工厂 (Crit Damage Boost Buff):
    在指定持续时间内提升自身暴击伤害倍率。
    - PUA 图标为暴击标志 (\uE406)，配色为金黄琥珀色 (F59E0B / D97706)。
    """
    if not appr_id:
        appr_id = f"appr_{mod_id}"

    validate_color_code(color_hex, "crit_damage_tc")
    validate_color_code(gradient_bottom, "crit_damage_gb")

    appear = {
        "id": appr_id,
        "a": callout_text,
        "s": "",
        "l": f"暴击伤害提升{int(crit_dmg_bonus*100)}%",
        "ss": f"暴击伤害提升{int(crit_dmg_bonus*100)}%",
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
        "t": "crit_damage",
        "tm": "",
        "tr": [trigger],
        "uit": [trigger],
        "pri": 0,
        "trm": 0.0,
        "trs": trigger_scope,
        "trr": "repeat",
        "c": float(chance),
        "m": float(crit_dmg_bonus),
        "d": float(duration),
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "crit_damage",
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


def make_remove_statmod(
    mod_id: str,
    target_mod_id: str,
    trigger: str = "onPlayerStateEnter",
    trigger_scope: str = "state=EvadeMelee",
    callout_text: str = "规避",
    appr_id: str = "",
    pua_icon: str = "\uE509",
    color_hex: str = "10B981",
    gradient_bottom: str = "059669",
    show_callout: bool = True,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    通用移除 Buff 修饰器工厂 (Remove Buff StatMod Factory):
    - 当满足特定触发条件时 (如进入 EvadeMelee / EvadeRanged 状态)，
      通过客户端原生 Remove_BuffEffect 移除指定的 Buff (target_mod_id)；
    - 可配置 callout 呼出文字 (如 '规避') 与 PUA 图标。
    """
    if not appr_id:
        appr_id = f"appr_{mod_id}"

    validate_color_code(color_hex, "remove_tc")
    validate_color_code(gradient_bottom, "remove_gb")

    appear = {
        "id": appr_id,
        "a": callout_text,
        "s": "",
        "l": f"触发{callout_text}",
        "ss": f"触发{callout_text}",
        "t": pua_icon,
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
        "t": "remove",
        "tm": target_mod_id,
        "tr": [trigger],
        "uit": [trigger],
        "pri": 0,
        "trm": 0.0,
        "trs": trigger_scope,
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


def make_armor_up_statmod(
    mod_id: str,
    duration: float,
    armor_bonus: float = 0.165,
    chance: float = 1.0,
    trigger: str = "onPlayerStateEnter",
    trigger_scope: str = "state=Block",
    appr_id: str = "",
    callout_text: str = "护甲",
    show_callout: bool = True,
    pua_icon: str = "\uE517",
    color_hex: str = "29EBF4",
    gradient_bottom: str = "00C5E8",
    stackable: bool = True,
    max_stacks: int = 10,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    通用护甲增益工厂 (Armor Up Buff Factory):
    提升目标 ArmorUpModifier，降低受到的伤害（减伤）。
    公式: damage *= (1.0 - GetArmorDR())，GetArmorDR() 累加 ArmorUpModifier。
    - PUA 矢量图标: 完整胸甲 (\uE517)
    - 配色: 官方电光青/青蓝 (29EBF4 / 00C5E8)
    """
    if not appr_id:
        appr_id = f"appr_{mod_id}"

    validate_color_code(color_hex, "armor_up_tc")
    validate_color_code(gradient_bottom, "armor_up_gb")

    appear = {
        "id": appr_id,
        "a": callout_text,
        "s": "",
        "l": f"获得护甲增益，降低受到伤害的{int(armor_bonus*100)}%",
        "ss": f"获得护甲增益，降低受到伤害的{int(armor_bonus*100)}%",
        "t": pua_icon,
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
        "t": "armor_up",
        "tm": "",
        "tr": [trigger],
        "uit": [trigger] if show_callout else [],
        "pri": 0,
        "trm": 0.0,
        "trs": trigger_scope,
        "trr": "repeat",
        "c": float(chance),
        "m": float(armor_bonus),
        "d": float(duration),
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": max_stacks if stackable else 1,
        "g": "armor_up",
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
    return {mod_id: stat_mod}, {appr_id: appear}


def make_armor_break_statmod(
    mod_id: str,
    duration: float,
    break_amount: float = 0.20,
    chance: float = 1.0,
    trigger: str = "onHit",
    trigger_scope: str = "level=Special1",
    appr_id: str = "",
    callout_text: str = "破甲",
    show_callout: bool = True,
    pua_icon: str = "\uE516",
    color_hex: str = "EF4444",
    gradient_bottom: str = "B91C1C",
    stackable: bool = True,
    max_stacks: int = 10,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    通用破甲减益工厂 (Armor Break Debuff Factory):
    施加于对手，提升 ArmorBreakModifier，放大对手受到的伤害。
    同时底层 ArmorBreak_BuffEffect.OnAdd 自动移除对手 1 层 armor_up 护甲增益。
    - PUA 矢量图标: 破甲碎盾 (\uE516)
    - 配色: 减益红/深红 (EF4444 / B91C1C)
    """
    if not appr_id:
        appr_id = f"appr_{mod_id}"

    validate_color_code(color_hex, "armor_break_tc")
    validate_color_code(gradient_bottom, "armor_break_gb")

    appear = {
        "id": appr_id,
        "a": callout_text,
        "s": "",
        "l": f"受到破甲减益，承受伤害增加{int(break_amount*100)}%",
        "ss": f"受到破甲减益，承受伤害增加{int(break_amount*100)}%",
        "t": pua_icon,
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
        "t": "armor_break",
        "tm": "",
        "tr": [trigger],
        "uit": [trigger] if show_callout else [],
        "pri": 0,
        "trm": 0.0,
        "trs": trigger_scope,
        "trr": "repeat",
        "c": float(chance),
        "m": float(break_amount),
        "d": float(duration),
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": max_stacks if stackable else 1,
        "g": "armor_break",
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
    return {mod_id: stat_mod}, {appr_id: appear}


def make_attack_boost_statmod(
    mod_id: str,
    duration: float,
    attack_bonus: float = 0.20,
    chance: float = 1.0,
    trigger: str = "onSpecial1Activate",
    trigger_scope: str = "",
    appr_id: str = "",
    callout_text: str = "攻击加成",
    show_callout: bool = True,
    pua_icon: str = "\uE406",
    color_hex: str = "F59E0B",
    gradient_bottom: str = "D97706",
    stackable: bool = True,
    max_stacks: int = 5,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    通用攻击力增益工厂 (Attack Boost Buff Factory):
    提升自身攻击力倍率。
    - PUA 矢量图标: 剑/暴击 (\uE406)
    - 配色: 金色/琥珀 (F59E0B / D97706)
    """
    if not appr_id:
        appr_id = f"appr_{mod_id}"

    validate_color_code(color_hex, "attack_boost_tc")
    validate_color_code(gradient_bottom, "attack_boost_gb")

    appear = {
        "id": appr_id,
        "a": callout_text,
        "s": "",
        "l": f"攻击力提升{int(attack_bonus*100)}%",
        "ss": f"攻击力提升{int(attack_bonus*100)}%",
        "t": pua_icon,
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
        "t": "attack_buff",
        "tm": "",
        "tr": [trigger],
        "uit": [trigger] if show_callout else [],
        "pri": 0,
        "trm": 0.0,
        "trs": trigger_scope,
        "trr": "repeat",
        "c": float(chance),
        "m": float(attack_bonus),
        "d": float(duration),
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": max_stacks if stackable else 1,
        "g": "attack_buff",
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
    return {mod_id: stat_mod}, {appr_id: appear}


def make_burn_statmod(
    mod_id: str,
    duration: float,
    total_dmg: float,
    chance: float = 1.0,
    trigger: str = "onHit",
    trigger_scope: str = "level=Heavy",
    appr_id: str = "",
    callout_text: str = "燃烧",
    is_zh: bool = True,
    stackable: bool = True,
    max_stacks: int = 10,
    target_scope: str = "none",
    target_actor: str = "opponent",
    pua_icon: str = "\uE41D",
    color_hex: str = "FF6600",
    gradient_bottom: str = "CC3300",
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    通用燃烧 DOT 工厂 (Burn DOT Factory):
    造成持续火焰/能量伤害 (Energy Damage over time)。
    - PUA 矢量图标: 火焰 (\uE41D)
    - 配色: 亮橙/深橙红 (FF6600 / CC3300)
    """
    if not appr_id:
        appr_id = f"appr_{mod_id}"

    validate_color_code(color_hex, "burn_tc")
    validate_color_code(gradient_bottom, "burn_gb")

    appear = {
        "id": appr_id,
        "a": callout_text,
        "s": "",
        "l": f"{callout_text}持续能量伤害",
        "ss": f"{callout_text}持续能量伤害",
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
        "t": "dmg_burn",
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
        "st": max_stacks if stackable else 1,
        "g": "dmg_burn",
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


def make_power_lock_statmod(
    mod_id: str,
    duration: float = 16.0,
    chance: float = 1.0,
    trigger: str = "onSpecial3Activate",
    trigger_scope: str = "",
    appr_id: str = "appr_power_lock",
    callout_text: str = "能量锁定",
    pua_icon: str = "\uE523",
    color_hex: str = "FF0000",
    gradient_bottom: str = "FF0000",
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    通用能量锁定工厂 (Power Lock Debuff):
    在指定持续时间内阻止对手获得能量 (Prevents opponent from gaining power over duration)。
    - 底层对接官方原生 'power_gain' BuffEffect 并传入微量负值(-0.01)压制气槽，同时由 Native Hook 拦截 AddMana 归零。
    - PUA 图标为能量锁定 (\uE523)，配色为减益红 (FF0000 / FF0000)。
    """
    validate_color_code(color_hex, "power_lock_tc")
    validate_color_code(gradient_bottom, "power_lock_gb")

    appear = {
        "id": appr_id,
        "a": callout_text,
        "s": "",
        "l": "阻止对手获得能量",
        "ss": "阻止对手获得能量",
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
        "t": "power_lock",
        "tm": "",
        "tr": [trigger],
        "uit": [trigger],
        "pri": 0,
        "trm": 0.0,
        "trs": trigger_scope,
        "trr": "repeat",
        "c": float(chance),
        "m": 1.0,  # 1.0 sets PowerLock = 1.0 so (1f - PowerLock) becomes 0.0 in PlayerAttributes.ApplyManaGain
        "d": float(duration),
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "power_lock_debuff",
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



