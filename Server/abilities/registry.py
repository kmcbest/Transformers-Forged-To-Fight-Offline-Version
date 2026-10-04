#!/usr/bin/env python3
"""
TFTF Bot Ability Dynamic Registry
=================================
负责自动发现、注册和装配 Server/abilities/bots/ 目录下的所有独立机器人能力模块。
"""

import importlib
import pkgutil
from pathlib import Path
from typing import Dict, Any, Callable, List

# 全局机器人模块注册表: { bot_id: registration_info }
_BOT_REGISTRY: Dict[str, Dict[str, Any]] = {}


def register_bot(bot_id: str, name_zh: str = "", desc: str = ""):
    """装饰器：将机器人能力生成函数注册进总能力引擎。"""
    def decorator(fn: Callable):
        _BOT_REGISTRY[bot_id] = {
            "bot_id": bot_id,
            "name_zh": name_zh,
            "desc": desc,
            "builder": fn,
        }
        return fn
    return decorator


def load_all_bots():
    """动态扫描并加载 Server/abilities/bots/ 目录下的全部机器人能力模块。"""
    bots_dir = Path(__file__).resolve().parent / "bots"
    if not bots_dir.exists():
        return

    # 遍历 bots 目录下的所有 python 模块
    for _, module_name, is_pkg in pkgutil.iter_modules([str(bots_dir)]):
        if not is_pkg and not module_name.startswith("_"):
            full_module = f"abilities.bots.{module_name}"
            try:
                importlib.import_module(full_module)
            except Exception as e:
                # 兼容从 Server 目录外部导入时的相对路径
                try:
                    importlib.import_module(f"Server.abilities.bots.{module_name}")
                except Exception as e2:
                    print(f"[WARN][Ability Registry] 加载机器人模块 {module_name} 失败: {e2}")


def get_registered_bots() -> List[str]:
    """返回所有已完成能力注册的机器人 ID 列表。"""
    load_all_bots()
    return list(_BOT_REGISTRY.keys())


def get_bot_mod_ids(bot_id: str) -> List[str]:
    """返回指定机器人绑定的专属能力修饰器 ID 列表。"""
    load_all_bots()
    reg = _BOT_REGISTRY.get(bot_id)
    if not reg:
        return []
    builder = reg["builder"]
    res = builder(base_hp=30000.0, base_atk=3000.0)
    if isinstance(res, (tuple, list)) and len(res) >= 1:
        mods = res[0]
    else:
        mods = res
    return list(mods.keys())


def collect_all_bot_statmods_and_appears() -> tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """收集所有已注册机器人的全部 StatMods、StatModAppears 以及额外 Buff 声明。"""
    load_all_bots()
    all_mods = {}
    all_appears = {}
    extra_buffs = {}

    for bot_id, reg in _BOT_REGISTRY.items():
        builder = reg["builder"]
        try:
            # 暂时传入基准属性构建默认配置
            res = builder(base_hp=34850.0, base_atk=3485.0)
            if len(res) == 2:
                mods, appears = res
                b_buffs = {}
            elif len(res) >= 3:
                mods, appears, b_buffs = res[0], res[1], res[2]
            else:
                mods, appears, b_buffs = {}, {}, {}

            all_mods.update(mods)
            all_appears.update(appears)
            extra_buffs.update(b_buffs)
        except Exception as e:
            print(f"[ERROR][Ability Registry] 执行机器人 {bot_id} 技能构建失败: {e}")

    return all_mods, all_appears, extra_buffs
