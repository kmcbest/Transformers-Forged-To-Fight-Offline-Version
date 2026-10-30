#!/usr/bin/env python3
"""
TFTF Character Profiles Engine
==============================
负责加载 78 位英雄官方技能与羁绊数据，优先从明文 JSON 目录 (Server/character_data/{bid}.json) 读取，
若不存在则回退从 Server/tftf_database.db 读取。

核心产出：
1. 招牌能力 (Signature Ability):
   - stat_modifier: f"sig_{bid}", uit: ["none"] (匹配官方汉化“被动”)
   - appearance: f"appr_sig_{bid}", s=title_zh, l=clean_desc, t=pua_icon (不猜测，无图标则为空)
2. 机体能力 (Abilities: basic & passive):
   - stat_modifier: f"ability_{bid}_{idx}", uit: [ui_trigger] ("none" -> 被动, "onHeavyHit" -> 重击等)
   - appearance: f"appr_ability_{bid}_{idx}", s=(title if show_on_main_screen else ""), l=clean_desc, t=pua_icon
3. 特殊攻击 (SP1 / SP2 / SP3):
   - stat_modifier: f"sp_ui_{bid}_{lvl}", uit: [f"onSpecial{lvl}Hit"] (匹配官方“特殊攻击 1/2/3”)
   - appearance: f"appr_sp_ui_{bid}_{lvl}", s="", l=clean_desc, t=pua_icon
4. 协同奖励 (Synergy Bonuses):
   - blueprints[bid]["sb"]: [syn_id_1, syn_id_2, ...]
   - loginData["synergyBonuses"][syn_id]: BCGSynergyBonus 完整契约字典
"""

import sqlite3
import json
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple, Any

ROOT_DIR = Path(__file__).resolve().parent
CHAR_DATA_DIR = ROOT_DIR / "character_data"
DB_PATH = ROOT_DIR / "tftf_database.db"

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
    """仅当显式配置了 16 进制字符时转换，绝不猜测。若为空则严格返回空字符串。"""
    if not pua_str:
        return ""
    s = str(pua_str).strip().lower()
    if s.startswith("0x"):
        s = s[2:]
    if s.startswith("\\u"):
        s = s[2:]
    try:
        val = int(s, 16)
        return chr(val) if val > 0 else ""
    except Exception:
        return ""


def _clean_comment(text: str) -> str:
    """去除每一行 // 之后的注释内容，并清理多余空行。保证游戏内说明文本纯净。"""
    if not text:
        return ""
    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        if "//" in line:
            line = line.split("//")[0]
        cleaned_lines.append(line.rstrip())
    res = "\n".join(cleaned_lines)
    return re.sub(r'\n{3,}', '\n\n', res).strip()


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


def _choose_ability_colors(title: str, desc: str) -> Tuple[str, str, str]:
    """根据能力效果类别返回对应 UI 颜色三元组 (tc, gt, gb)。"""
    text = (title + " " + desc).lower()
    if any(k in text for k in ["流血", "燃烧", "震击", "强酸", "破甲", "眩晕", "流失", "锁定"]):
        return ("EF4444", "DC2626", "B91C1C")
    elif any(k in text for k in ["护盾", "防御", "不可阻挡", "装甲"]):
        return ("3B82F6", "2563EB", "1D4ED8")
    elif any(k in text for k in ["修复", "回血", "治愈"]):
        return ("10B981", "059669", "047857")
    elif any(k in text for k in ["能量", "充能"]):
        return ("8B5CF6", "7C3AED", "6D28D9")
    elif any(k in text for k in ["暴击", "攻击", "伤害", "暴发"]):
        return ("F59E0B", "D97706", "B45309")
    return ("FFFFFF", "FFFFFF", "FFFFFF")


def _init_profiles():
    global _INITIALIZED
    if _INITIALIZED:
        return

    # 优先检测明文 JSON 目录 (Server/character_data)
    json_files = list(CHAR_DATA_DIR.glob("*.json")) if CHAR_DATA_DIR.exists() else []
    if json_files:
        _init_from_json_files(json_files)
    elif DB_PATH.exists():
        _init_from_database()
    else:
        print(f"[WARN] Neither {CHAR_DATA_DIR} nor {DB_PATH} found!")

    _INITIALIZED = True


def _init_from_json_files(json_files: List[Path]):
    """从 Server/character_data/*.json 明文文件加载所有角色技能与协同。"""
    for jpath in json_files:
        try:
            with open(jpath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"[ERROR] Failed to load {jpath}: {e}")
            continue

        bot_id = data.get("bot_id")
        if not bot_id:
            continue

        _BOT_UI_MOD_IDS[bot_id] = []

        # 1. 招牌能力 (Signature)
        sig = data.get("signature", {})
        if sig and (sig.get("title_zh") or sig.get("title_en")):
            mod_id = f"sig_{bot_id}"
            appr_id = f"appr_sig_{bot_id}"
            clean_desc = _clean_comment(sig.get("desc_zh", ""))
            icon_char = _hex_to_pua_char(sig.get("pua_icon", ""))
            name = sig.get("title_zh") or sig.get("title_en")
            tc, gt, gb = _choose_ability_colors(name, clean_desc)
            uit_val = sig.get("ui_trigger", "none")

            _SIG_MODS[mod_id] = {
                "id": mod_id,
                "AppearanceID": appr_id,
                "Type": "combat",
                "t": "combat",
                "d": 0.0,
                "m": 0.0,
                "p": 1.0,
                "tr": ["always"],
                "uit": [uit_val],
                "a": [appr_id],
                "au": [],
                "rh": 0.0,
                "ra": 0.0,
            }
            _SIG_APPEARS[appr_id] = {
                "id": appr_id,
                "a": name,
                "s": name,
                "ss": clean_desc,
                "l": clean_desc,
                "t": icon_char,
                "tc": tc,
                "gt": gt,
                "gb": gb,
            }

        # 2. 机体能力 (Abilities: basic & passive)
        abilities_list = data.get("abilities", [])
        for idx, ab in enumerate(abilities_list):
            mod_id = f"ability_{bot_id}_{idx}"
            appr_id = f"appr_ability_{bot_id}_{idx}"
            clean_desc = _clean_comment(ab.get("desc_zh", ""))
            icon_char = _hex_to_pua_char(ab.get("pua_icon", ""))
            name = ab.get("title_zh") or ab.get("title_en")
            tc, gt, gb = _choose_ability_colors(name, clean_desc)
            ui_tr = ab.get("ui_trigger", "none")
            show_main = ab.get("show_on_main_screen", True)

            _BOT_UI_MOD_IDS[bot_id].append(mod_id)
            _UI_MODS[mod_id] = {
                "id": mod_id,
                "AppearanceID": appr_id,
                "Type": "combat",
                "t": "combat",
                "d": 0.0,
                "m": 0.0,
                "p": 1.0,
                "tr": [ui_tr] if ui_tr != "none" else [],
                "uit": [ui_tr],
                "a": [appr_id],
                "au": [],
                "rh": 0.0,
                "ra": 0.0,
            }
            _UI_APPEARS[appr_id] = {
                "id": appr_id,
                "a": name,
                "s": name if show_main else "",  # ShortStringID 非空时挂入主界面能力列表
                "ss": clean_desc,
                "l": clean_desc,                 # LongStringID 非空时展开至对应触发器分类
                "t": icon_char,
                "tc": tc,
                "gt": gt,
                "gb": gb,
            }

        # 3. 特殊攻击 (SP1 / SP2 / SP3)
        specials = data.get("special_attacks", {})
        for sp_idx, cat in enumerate(["sp1", "sp2", "sp3"], start=1):
            sp_data = specials.get(cat, {})
            if not sp_data:
                continue
            name = sp_data.get("name_zh") or sp_data.get("name_en") or f"SP{sp_idx}"
            clean_desc = _clean_comment(sp_data.get("desc_zh", ""))
            if not clean_desc:
                continue
            icon_char = _hex_to_pua_char(sp_data.get("pua_icon", ""))
            mod_id = f"sp_ui_{bot_id}_{sp_idx}"
            appr_id = f"appr_sp_ui_{bot_id}_{sp_idx}"
            tc, gt, gb = _choose_ability_colors(name, clean_desc)
            ui_tr = sp_data.get("ui_trigger", f"onSpecial{sp_idx}Hit")

            _BOT_UI_MOD_IDS[bot_id].append(mod_id)
            _UI_MODS[mod_id] = {
                "id": mod_id,
                "AppearanceID": appr_id,
                "Type": "combat",
                "t": "combat",
                "d": 0.0,
                "m": 0.0,
                "p": 1.0,
                "tr": [ui_tr],
                "uit": [ui_tr],
                "a": [appr_id],
                "au": [],
                "rh": 0.0,
                "ra": 0.0,
            }
            _UI_APPEARS[appr_id] = {
                "id": appr_id,
                "a": name,
                "s": "",                         # 不抢占主界面的基础能力名额
                "ss": "",
                "l": clean_desc,
                "t": icon_char,
                "tc": tc,
                "gt": gt,
                "gb": gb,
            }

        # 4. 协同奖励 (Synergies)
        synergies_list = data.get("synergies", [])
        for syn_idx, syn in enumerate(synergies_list):
            syn_id = f"syn_{bot_id}_{syn_idx}"
            if bot_id not in _BOT_SYNERGY_IDS:
                _BOT_SYNERGY_IDS[bot_id] = []
            _BOT_SYNERGY_IDS[bot_id].append(syn_id)
            clean_desc = _clean_comment(syn.get("desc_zh", ""))
            syn_title = syn.get("title_zh") or syn.get("title_en")
            tex = _hex_to_pua_char(syn.get("pua_icon", "")) or _choose_synergy_icon(syn_title, clean_desc)
            _SYNERGY_BONUSES[syn_id] = {
                "id": syn_id,
                "s": syn_title,
                "e": True,
                "t": syn.get("bonus_heroes", []),
                "st": tex,
                "sb": clean_desc,
                "l": clean_desc,
                "a": [],
            }


def _init_from_database():
    """回退方式：直接从 Server/tftf_database.db 读取。"""
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    cur.execute("SELECT bot_id, title_zh, title_en, desc_zh, pua_icon FROM character_abilities WHERE category='signature'")
    for bot_id, title_zh, title_en, desc_zh, pua_icon in cur.fetchall():
        mod_id = f"sig_{bot_id}"
        appr_id = f"appr_sig_{bot_id}"
        clean_desc = _clean_comment(desc_zh)
        icon_char = _hex_to_pua_char(pua_icon)
        name = title_zh if title_zh else title_en
        tc, gt, gb = _choose_ability_colors(title_zh, clean_desc)

        _SIG_MODS[mod_id] = {
            "id": mod_id,
            "AppearanceID": appr_id,
            "Type": "combat",
            "t": "combat",
            "d": 0.0,
            "m": 0.0,
            "p": 1.0,
            "tr": ["always"],
            "uit": ["none"],
            "a": [appr_id],
            "au": [],
            "rh": 0.0,
            "ra": 0.0,
        }
        _SIG_APPEARS[appr_id] = {
            "id": appr_id,
            "a": name,
            "s": name,
            "ss": clean_desc,
            "l": clean_desc,
            "t": icon_char,
            "tc": tc,
            "gt": gt,
            "gb": gb,
        }

    cur.execute("SELECT DISTINCT bot_id FROM characters")
    all_bots = [r[0] for r in cur.fetchall()]

    for bot_id in all_bots:
        _BOT_UI_MOD_IDS[bot_id] = []
        cur.execute(
            "SELECT id, category, title_zh, title_en, desc_zh, pua_icon FROM character_abilities "
            "WHERE bot_id=? AND category IN ('basic', 'passive') ORDER BY sort_order",
            (bot_id,),
        )
        for idx, (row_id, ab_cat, title_zh, title_en, desc_zh, pua_icon) in enumerate(cur.fetchall()):
            if not title_zh or "基础特长" in title_zh:
                continue
            mod_id = f"ability_{bot_id}_{idx}"
            appr_id = f"appr_ability_{bot_id}_{idx}"
            clean_desc = _clean_comment(desc_zh)
            icon_char = _hex_to_pua_char(pua_icon)
            name = title_zh if title_zh else title_en
            tc, gt, gb = _choose_ability_colors(title_zh, clean_desc)

            ui_tr = "onHeavyHit" if "重击" in title_zh else "none"
            _BOT_UI_MOD_IDS[bot_id].append(mod_id)
            _UI_MODS[mod_id] = {
                "id": mod_id,
                "AppearanceID": appr_id,
                "Type": "combat",
                "t": "combat",
                "d": 0.0,
                "m": 0.0,
                "p": 1.0,
                "tr": [ui_tr] if ui_tr != "none" else [],
                "uit": [ui_tr],
                "a": [appr_id],
                "au": [],
                "rh": 0.0,
                "ra": 0.0,
            }
            _UI_APPEARS[appr_id] = {
                "id": appr_id,
                "a": name,
                "s": name,
                "ss": clean_desc,
                "l": clean_desc,
                "t": icon_char,
                "tc": tc,
                "gt": gt,
                "gb": gb,
            }

        cur.execute("SELECT sp1_name_zh, sp2_name_zh, sp3_name_zh FROM characters WHERE bot_id=?", (bot_id,))
        sp_custom_row = cur.fetchone()
        sp_custom_names = list(sp_custom_row) if sp_custom_row else ["", "", ""]

        for sp_idx, cat in enumerate(["sp1", "sp2", "sp3"], start=1):
            cur.execute(
                "SELECT id, title_zh, title_en, desc_zh, pua_icon FROM character_abilities "
                "WHERE bot_id=? AND category=? ORDER BY sort_order",
                (bot_id, cat),
            )
            sp_row = cur.fetchone()
            if not sp_row:
                continue
            row_id, title_zh, title_en, desc_zh, pua_icon = sp_row
            mod_id = f"sp_ui_{bot_id}_{sp_idx}"
            appr_id = f"appr_sp_ui_{bot_id}_{sp_idx}"
            clean_desc = _clean_comment(desc_zh)
            icon_char = _hex_to_pua_char(pua_icon)
            name = sp_custom_names[sp_idx - 1] or title_zh or title_en
            tc, gt, gb = _choose_ability_colors(title_zh, clean_desc)
            ui_tr = f"onSpecial{sp_idx}Hit"

            _BOT_UI_MOD_IDS[bot_id].append(mod_id)
            _UI_MODS[mod_id] = {
                "id": mod_id,
                "AppearanceID": appr_id,
                "Type": "combat",
                "t": "combat",
                "d": 0.0,
                "m": 0.0,
                "p": 1.0,
                "tr": [ui_tr],
                "uit": [ui_tr],
                "a": [appr_id],
                "au": [],
                "rh": 0.0,
                "ra": 0.0,
            }
            _UI_APPEARS[appr_id] = {
                "id": appr_id,
                "a": name,
                "s": "",
                "ss": "",
                "l": clean_desc,
                "t": icon_char,
                "tc": tc,
                "gt": gt,
                "gb": gb,
            }

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

        clean_desc = _clean_comment(desc_zh)
        syn_title = title_zh if title_zh else title_en
        tex = _hex_to_pua_char(pua_icon) or _choose_synergy_icon(syn_title, clean_desc)

        _SYNERGY_BONUSES[syn_id] = {
            "id": syn_id,
            "s": syn_title,
            "e": True,
            "t": bonus_heroes,
            "st": tex,
            "sb": clean_desc,
            "l": clean_desc,
            "a": [],
        }


def get_bot_sig_mod_id(bot_id: str) -> str:
    _init_profiles()
    mod_id = f"sig_{bot_id}"
    return mod_id if mod_id in _SIG_MODS else ""


def get_bot_ui_ability_ids(bot_id: str) -> List[str]:
    _init_profiles()
    return _BOT_UI_MOD_IDS.get(bot_id, [])


def get_bot_synergy_ids(bot_id: str) -> List[str]:
    _init_profiles()
    return _BOT_SYNERGY_IDS.get(bot_id, [])


def build_all_sig_mods() -> Dict[str, Dict[str, Any]]:
    _init_profiles()
    return dict(_SIG_MODS)


def build_all_sig_appears() -> Dict[str, Dict[str, Any]]:
    _init_profiles()
    return dict(_SIG_APPEARS)


def build_all_ui_mods() -> Dict[str, Dict[str, Any]]:
    _init_profiles()
    return dict(_UI_MODS)


def build_all_ui_appears() -> Dict[str, Dict[str, Any]]:
    _init_profiles()
    return dict(_UI_APPEARS)


def get_profile_stat_modifiers() -> Dict[str, Dict[str, Any]]:
    _init_profiles()
    res = {}
    res.update(_SIG_MODS)
    res.update(_UI_MODS)
    return res


def get_profile_stat_mod_appears() -> Dict[str, Dict[str, Any]]:
    _init_profiles()
    res = {}
    res.update(_SIG_APPEARS)
    res.update(_UI_APPEARS)
    return res


def build_all_synergy_bonuses(lang: str = "zh") -> Dict[str, Dict[str, Any]]:
    _init_profiles()
    return dict(_SYNERGY_BONUSES)
