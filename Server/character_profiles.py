#!/usr/bin/env python3
"""
TFTF Character Profiles Engine
==============================
负责从 Server/tftf_database.db 读取 78 位英雄官方技能与羁绊真理源，并生成：
1. 招牌能力 (Signature Ability):
   - stat_modifier: f"sig_{bid}"
   - appearance: f"appr_sig_{bid}", s=title_zh (用于 CharacterStatSummaryPanel.SuperSkillUI 展示)
2. 基础/被动能力 (UI Display Abilities):
   - stat_modifier: f"ability_{bid}_{idx}"
   - appearance: f"appr_ability_{bid}_{idx}", s=title_zh, ss=desc_zh, t=pua_icon
     (用于 CharacterStatSummaryPanel._abilitiesAligner 展示真实能力，如阿尔茜的“规避”、“爆头”)
3. 协同奖励 (Synergy Bonuses):
   - blueprints[bid]["sb"]: [syn_id_1, syn_id_2, ...]
   - loginData["synergyBonuses"][syn_id]: BCGSynergyBonus 完整契约字典 (Texture=PUA glyph)
"""

import sqlite3
import json
import os
from pathlib import Path
from typing import Dict, List, Tuple, Any

DB_PATH = Path(__file__).resolve().parent / "tftf_database.db"

# 内存缓存
_SIG_MODS: Dict[str, Dict[str, Any]] = {}
_SIG_APPEARS: Dict[str, Dict[str, Any]] = {}

_BOT_UI_MOD_IDS: Dict[str, List[str]] = {}
_UI_MODS: Dict[str, Dict[str, Any]] = {}
_UI_APPEARS: Dict[str, Dict[str, Any]] = {}

_BOT_SYNERGY_IDS: Dict[str, List[str]] = {}
_SYNERGY_BONUSES: Dict[str, Dict[str, Any]] = {}

_INITIALIZED = False


def _hex_to_pua_char(pua_str: str) -> str:
    if not pua_str:
        return ""
    s = pua_str.strip().lower()
    if s.startswith("0x"):
        s = s[2:]
    try:
        return chr(int(s, 16))
    except Exception:
        return ""


def _choose_synergy_icon(title: str, desc: str) -> str:
    text = (title + " " + desc).lower()
    if any(k in text for k in ["装甲", "armor", "防御", "defense"]):
        return chr(0xe501)  # shield_up
    elif any(k in text for k in ["攻击", "attack", "近战", "melee", "伤害", "damage", "暴击", "crit"]):
        return chr(0xe40d)  # punch / crit
    elif any(k in text for k in ["生命", "health", "hp", "医疗"]):
        return chr(0xe504)  # heart
    elif any(k in text for k in ["流血", "bleed"]):
        return chr(0xe401)  # bleed
    elif any(k in text for k in ["领袖", "leadership", "霸天虎"]):
        return chr(0xe133)  # decepticon
    elif any(k in text for k in ["汽车人"]):
        return chr(0xe132)  # autobot
    return chr(0xe501)  # default shield


def _init_profiles():
    global _INITIALIZED
    if _INITIALIZED:
        return
    if not DB_PATH.exists():
        print(f"[WARN] Database {DB_PATH} not found!")
        return

    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    # 1. 加载所有招牌能力 (Signature Abilities)
    cur.execute("SELECT bot_id, title_zh, title_en, desc_zh, pua_icon FROM character_abilities WHERE category='signature'")
    for bot_id, title_zh, title_en, desc_zh, pua_icon in cur.fetchall():
        mod_id = f"sig_{bot_id}"
        appr_id = f"appr_sig_{bot_id}"
        icon_char = _hex_to_pua_char(pua_icon) or chr(0xe40d)
        name = title_zh if title_zh else title_en

        _SIG_MODS[mod_id] = {
            "id": mod_id,
            "AppearanceID": appr_id,
            "Type": "combat",
            "t": "combat",
            "d": 0.0,
            "m": 0.0,
            "p": 1.0,
            "tr": ["always"],
            "uit": [],
            "a": [appr_id],
            "au": [],
            "rh": 0.0,
            "ra": 0.0,
        }
        _SIG_APPEARS[appr_id] = {
            "id": appr_id,
            "a": name,
            "s": name,          # ShortStringID -> 用于 SuperSkillUI _nameLabel 显示技能名称
            "ss": desc_zh,
            "l": desc_zh,
            "t": icon_char,
            "tc": "FFFFFF",
            "gt": "FFFFFF",
            "gb": "FFFFFF",
        }

    # 2. 加载 UI 展示能力 (Basic/Passive Abilities)
    cur.execute("SELECT DISTINCT bot_id FROM characters")
    all_bots = [r[0] for r in cur.fetchall()]

    for bot_id in all_bots:
        _BOT_UI_MOD_IDS[bot_id] = []
        # 优先读取非泛型 "基础特长" 的 basic 能力 (如阿尔茜的“规避”、“爆头”)
        cur.execute(
            "SELECT id, title_zh, title_en, desc_zh, pua_icon FROM character_abilities "
            "WHERE bot_id=? AND category='basic' AND title_zh != '基础特长' ORDER BY sort_order",
            (bot_id,),
        )
        selected_abilities = cur.fetchall()

        # 若无具名 basic 能力，则回退选取具名 passive 能力 (如钢锁的“近战强化”、“燃烧”)
        if not selected_abilities:
            cur.execute(
                "SELECT id, title_zh, title_en, desc_zh, pua_icon FROM character_abilities "
                "WHERE bot_id=? AND category='passive' ORDER BY sort_order",
                (bot_id,),
            )
            passives = cur.fetchall()
            seen_titles = set()
            for p in passives:
                t = p[1].strip()
                if not t or t in seen_titles or "基础特长" in t or t.startswith("受到") or t.startswith("重击") or t.startswith("战斗开始") or t.startswith("受到攻击"):
                    continue
                seen_titles.add(t)
                selected_abilities.append(p)
                if len(selected_abilities) >= 3:
                    break

        for idx, (row_id, title_zh, title_en, desc_zh, pua_icon) in enumerate(selected_abilities):
            mod_id = f"ability_{bot_id}_{idx}"
            appr_id = f"appr_ability_{bot_id}_{idx}"
            icon_char = _hex_to_pua_char(pua_icon)
            name = title_zh if title_zh else title_en

            _BOT_UI_MOD_IDS[bot_id].append(mod_id)
            _UI_MODS[mod_id] = {
                "id": mod_id,
                "AppearanceID": appr_id,
                "Type": "combat",
                "t": "combat",
                "d": 0.0,
                "m": 0.0,
                "p": 1.0,
                "tr": [],       # 纯 UI 展示能力，不注册战斗触发器以防副作用
                "uit": [],
                "a": [appr_id],
                "au": [],
                "rh": 0.0,
                "ra": 0.0,
            }
            _UI_APPEARS[appr_id] = {
                "id": appr_id,
                "a": name,
                "s": name,      # ShortStringID -> 用于 CharacterStatSummaryPanel._abilitiesAligner 创建 AbilityItem
                "ss": desc_zh,  # SimpleStringID -> 用于 AbilityItem._descriptionLabel
                "l": desc_zh,
                "t": icon_char, # IconTexture -> 用于 AbilityItem._iconLabel
                "tc": "FFFFFF",
                "gt": "FFFFFF",
                "gb": "FFFFFF",
            }

    # 3. 加载协同奖励 (Synergy Bonuses)
    cur.execute(
        "SELECT id, bot_id, title_zh, title_en, desc_zh, pua_icon, synergy_bots "
        "FROM character_abilities WHERE category='synergy' ORDER BY sort_order"
    )
    for row_id, bot_id, title_zh, title_en, desc_zh, pua_icon, synergy_bots_json in cur.fetchall():
        if bot_id not in _BOT_SYNERGY_IDS:
            _BOT_SYNERGY_IDS[bot_id] = []
        syn_id = f"syn_{bot_id}_{row_id}"
        _BOT_SYNERGY_IDS[bot_id].append(syn_id)

        try:
            bonus_heroes = json.loads(synergy_bots_json) if synergy_bots_json else []
        except Exception:
            bonus_heroes = []

        icon_char = _hex_to_pua_char(pua_icon) or _choose_synergy_icon(title_zh, desc_zh)
        name = title_zh if title_zh else title_en
        if not name and desc_zh and "-" in desc_zh:
            name = desc_zh.split("-")[0].strip()
        if not name:
            name = "协同加成"

        _SYNERGY_BONUSES[syn_id] = {
            "id": syn_id,
            "s": name,
            "sd": desc_zh,
            "sv": 0.15,
            "st": icon_char,    # Texture -> 用于 SynergyBonusTile._label.text 显示图标
            "b": [bot_id],      # BonusHeroes: 收益英雄（如阿尔茜）
            "r": bonus_heroes,  # RequiredHeroes: 协同搭档英雄列表（如幻影、探长，客户端据此展示头像并判定激活）
            "tt": [],
            "e": True,          # Enabled
            "rh": 0.0,
            "ra": 0.0,
            "sm": [],
        }

    conn.close()
    _INITIALIZED = True


def get_bot_sig_mod_id(bot_id: str) -> str:
    """获取指定机器人的招牌技能 Mod ID (如 'sig_arcee_gs_deluxe2014')。"""
    _init_profiles()
    mod_id = f"sig_{bot_id}"
    return mod_id if mod_id in _SIG_MODS else ""


def get_bot_ui_ability_ids(bot_id: str) -> List[str]:
    """获取指定机器人用于 UI 展示的基础能力 Mod ID 列表。"""
    _init_profiles()
    return list(_BOT_UI_MOD_IDS.get(bot_id, []))


def get_bot_synergy_ids(bot_id: str) -> List[str]:
    """获取指定机器人的协同奖励 ID 列表 (用于 blueprint['sb'])。"""
    _init_profiles()
    return list(_BOT_SYNERGY_IDS.get(bot_id, []))


def build_all_synergy_bonuses(lang: str = "zh") -> Dict[str, Dict[str, Any]]:
    """获取全局所有协同加成定义字典 (用于 getLoginData['synergyBonuses'])。"""
    _init_profiles()
    return dict(_SYNERGY_BONUSES)


def get_profile_stat_modifiers() -> Dict[str, Dict[str, Any]]:
    """汇总所有英雄的招牌与 UI 展示能力 StatModifiers。"""
    _init_profiles()
    res = {}
    res.update(_SIG_MODS)
    res.update(_UI_MODS)
    return res


def get_profile_stat_mod_appears() -> Dict[str, Dict[str, Any]]:
    """汇总所有英雄的招牌与 UI 展示能力外观配置。"""
    _init_profiles()
    res = {}
    res.update(_SIG_APPEARS)
    res.update(_UI_APPEARS)
    return res
