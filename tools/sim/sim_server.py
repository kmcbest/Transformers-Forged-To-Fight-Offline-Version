#!/usr/bin/env python3
"""
TFTF Desktop Combat Simulator Server (Data Contract & Lifecycle Upgraded)
========================================================================
Local HTTP Server providing Web UI and REST API for the Combat Sandbox.
Binds directly to Server/abilities/ official bot registry and enforces strict
game engine lifecycle emulation (onStart triggers) & visual data contracts.
"""
import os
import sys
import json
import sqlite3
import ctypes
import random
import webbrowser
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

SIM_DIR = REPO_ROOT / "tools/sim"
WEB_DIR = SIM_DIR / "web"
DB_PATH = REPO_ROOT / "Server/tftf_database.db"
DLL_PATH = SIM_DIR / "sim_skills.dll"

# ---------------------------------------------------------------------------
# 1. 官方能力数据库绑定 (Server/abilities/ 契约真理源)
# ---------------------------------------------------------------------------
from Server.abilities.registry import (
    load_all_bots,
    collect_all_bot_statmods_and_appears,
    _BOT_REGISTRY,
)

load_all_bots()
ALL_MODS, ALL_APPEARS, EXTRA_BUFFS = collect_all_bot_statmods_and_appears()
print(f"[SimServer] 已加载 Server/abilities 官方能力库: {len(ALL_MODS)} StatMods, {len(ALL_APPEARS)} Appearances, {len(_BOT_REGISTRY)} 注册角色.")

# 全局标准战斗 Buff 表 (客户端通用减益/增益标准外观)
STANDARD_BUFFS = {
    "dmg_bleed": {
        "pua": "0xE401", "pua_char": "\uE401", "name": "流血", "tc": "EF4444", "gb": "DC2626",
        "desc": "持续受到流血伤害", "is_contract_valid": True, "dur_s": 7.0
    },
    "burn": {
        "pua": "0xE41D", "pua_char": "\uE41D", "name": "灼烧", "tc": "F97316", "gb": "EA580C",
        "desc": "持续受到烈焰灼烧伤害", "is_contract_valid": True, "dur_s": 6.0
    },
    "shock": {
        "pua": "0xE914", "pua_char": "\uE914", "name": "震击", "tc": "EF4444", "gb": "B91C1C",
        "desc": "持续受到电磁震击伤害", "is_contract_valid": True, "dur_s": 6.0
    },
    "armor_break": {
        "pua": "0xE516", "pua_char": "\uE516", "name": "破甲", "tc": "EAB308", "gb": "CA8A04",
        "desc": "护甲大幅削弱，受到伤害增加", "is_contract_valid": True, "dur_s": 6.0
    },
    "armor_up": {
        "pua": "0xE517", "pua_char": "\uE517", "name": "护甲", "tc": "06B6D4", "gb": "0891B2",
        "desc": "护甲强化，受到伤害降低", "is_contract_valid": True, "dur_s": 7.0
    },
    "melee_buff": {
        "pua": "0xE412", "pua_char": "\uE412", "name": "近战增益", "tc": "F59E0B", "gb": "D97706",
        "desc": "近战伤害大幅提升", "is_contract_valid": True, "dur_s": 4.0
    },
    "crit_buff": {
        "pua": "0xE40D", "pua_char": "\uE40D", "name": "暴击增益", "tc": "EC4899", "gb": "DB2777",
        "desc": "暴击率大幅提升", "is_contract_valid": True, "dur_s": 8.0
    },
    "stun": {
        "pua": "0xE605", "pua_char": "\uE605", "name": "眩晕", "tc": "8B5CF6", "gb": "7C3AED",
        "desc": "陷入昏迷无法行动", "is_contract_valid": True, "dur_s": 2.5
    },
    "evade": {
        "pua": "0xE509", "pua_char": "\uE509", "name": "闪避/规避", "tc": "10B981", "gb": "059669",
        "desc": "规避受到的攻击", "is_contract_valid": True, "dur_s": 5.0
    },
    "decel": {
        "pua": "0xE952", "pua_char": "\uE952", "name": "时间减速", "tc": "6366F1", "gb": "4F46E5",
        "desc": "速度与时间减速", "is_contract_valid": True, "dur_s": 5.0
    },
    "unstoppable": {
        "pua": "0xE915", "pua_char": "\uE915", "name": "不可阻挡", "tc": "EF4444", "gb": "B91C1C",
        "desc": "免疫受击硬直与击退", "is_contract_valid": True, "dur_s": 4.0
    },
    "power_gain": {
        "pua": "0xE403", "pua_char": "\uE403", "name": "能量获取", "tc": "38BDF8", "gb": "0284C7",
        "desc": "战斗能量获取速率大幅提升", "is_contract_valid": True, "dur_s": 8.0
    },
    "power_buff": {
        "pua": "0xE403", "pua_char": "\uE403", "name": "能量增益", "tc": "38BDF8", "gb": "0284C7",
        "desc": "持有能量获取增益效果", "is_contract_valid": True, "dur_s": 8.0
    },
    "power_steal": {
        "pua": "0xE606", "pua_char": "\uE606", "name": "能量窃取", "tc": "06B6D4", "gb": "0891B2",
        "desc": "持续窃取对手能量", "is_contract_valid": True, "dur_s": 6.0
    },
    "power_lock": {
        "pua": "0xE606", "pua_char": "\uE606", "name": "能量锁定", "tc": "64748B", "gb": "475569",
        "desc": "能量被封锁无法增加", "is_contract_valid": True, "dur_s": 5.0
    },
    "shield": {
        "pua": "0xE518", "pua_char": "\uE518", "name": "防护力场", "tc": "38BDF8", "gb": "0369A1",
        "desc": "吸收即将受到的伤害", "is_contract_valid": True, "dur_s": 6.0
    },
    "dmg_poison": {
        "pua": "0xE402", "pua_char": "\uE402", "name": "酸蚀中毒", "tc": "10B981", "gb": "047857",
        "desc": "持续受到酸蚀伤害", "is_contract_valid": True, "dur_s": 6.0
    },
    "crit_damage_buff": {
        "pua": "0xE406", "pua_char": "\uE406", "name": "爆伤增益", "tc": "F43F5E", "gb": "BE123C",
        "desc": "暴击伤害倍率提升", "is_contract_valid": True, "dur_s": 8.0
    },
    "atk_buff": {
        "pua": "0xE406", "pua_char": "\uE406", "name": "攻击强化", "tc": "F59E0B", "gb": "B45309",
        "desc": "基础攻击力提升", "is_contract_valid": True, "dur_s": 8.0
    },
    "atk_debuff": {
        "pua": "0xE408", "pua_char": "\uE408", "name": "虚弱削弱", "tc": "94A3B8", "gb": "64748B",
        "desc": "攻击力降低", "is_contract_valid": True, "dur_s": 6.0
    },
    "heal_block": {
        "pua": "0xE950", "pua_char": "\uE950", "name": "禁疗诅咒", "tc": "A855F7", "gb": "7E22CE",
        "desc": "无法恢复生命值", "is_contract_valid": True, "dur_s": 8.0
    },
}

# 关键词映射 PUA 图标回退表 (游戏标准图标库)
PUA_FALLBACKS = [
    (r"流血|破血|割伤|撕裂", "0xe401"),
    (r"灼烧|焚烧|烈焰|点燃|火", "0xe41d"),
    (r"震击|感电|电击|闪电", "0xe914"),
    (r"破甲|碎甲|削甲", "0xe516"),
    (r"护甲|防御|盾|减伤", "0xe517"),
    (r"近战", "0xe412"),
    (r"攻击|增伤|狂暴|力量", "0xe406"),
    (r"虚弱|弱化|攻击降低", "0xe408"),
    (r"暴击率|专注", "0xe40d"),
    (r"暴击伤害|爆伤", "0xe406"),
    (r"意志力|坚韧", "0xe942"),
    (r"净化", "0xe942"),
    (r"驱散|抵消", "0xe950"),
    (r"规避|闪避|后退|躲闪", "0xe509"),
    (r"眩晕|昏迷|麻痹", "0xe605"),
    (r"减速|迟缓|时间场", "0xe952"),
    (r"能量获取|充能|回气", "0xe403"),
    (r"能量流失|吸气|能量偷取", "0xe607"),
    (r"不可阻挡|霸体|无畏", "0xe915"),
    (r"吸血|修复|治疗|生命回复", "0xe50b"),
]

def guess_pua(title, desc):
    import re
    text = (title or "") + " " + (desc or "")
    for pat, pua in PUA_FALLBACKS:
        if re.search(pat, text):
            return pua
    return "0xe406"

def decorate_buff(buff):
    """为底层 C 返回的 buff 字典装饰官方数据库外观与契约校验标记。"""
    bid = buff.get("id", "")
    # 1. 优先从 Server/abilities/ 官方能力库检索
    if bid in ALL_MODS:
        mod = ALL_MODS[bid]
        app_ids = mod.get("a", [])
        app = ALL_APPEARS.get(app_ids[0], {}) if app_ids else {}
        pua_char = app.get("t", "")
        pua_hex = ("0x" + hex(ord(pua_char))[2:].upper()) if pua_char else "0xE406"
        name = app.get("a") or app.get("s") or app.get("ps") or app.get("ss") or bid
        tc = app.get("tc", "FFFFFF")
        gb = app.get("gb", tc)
        desc = app.get("l") or app.get("pl") or ""
        dur_s = float(mod.get("d", 0.0))
        return {
            **buff,
            "pua": pua_hex,
            "pua_char": pua_char,
            "name": name,
            "tc": tc,
            "gb": gb,
            "desc": desc,
            "dur_s": dur_s,
            "is_contract_valid": True,
        }

    # 2. 从官方通用战斗 Buff 表检索
    for pattern, sinfo in STANDARD_BUFFS.items():
        if pattern == bid or pattern in bid:
            return {
                **buff,
                **sinfo,
            }

    # 3. 从额外注册 Buff 表检索
    if bid in EXTRA_BUFFS:
        eb = EXTRA_BUFFS[bid]
        pua_char = eb.get("t", "")
        pua_hex = ("0x" + hex(ord(pua_char))[2:].upper()) if pua_char else "0xE406"
        return {
            **buff,
            "pua": pua_hex,
            "pua_char": pua_char,
            "name": eb.get("a") or bid,
            "tc": eb.get("tc", "FFFFFF"),
            "gb": eb.get("gb", "888888"),
            "desc": eb.get("l", ""),
            "dur_s": float(eb.get("d", 0.0)),
            "is_contract_valid": True,
        }

    # 4. 未在任何官方配置中找到 -> 标记契约违规 (Contract Violation)
    pua_guess = guess_pua(bid, "")
    try:
        pua_char = chr(int(pua_guess, 16))
    except Exception:
        pua_char = "\uE406"
    return {
        **buff,
        "pua": pua_guess,
        "pua_char": pua_char,
        "name": bid,
        "tc": "94A3B8",
        "gb": "64748B",
        "desc": f"未在 Server/abilities/ 官方库注册的 Buff ID: {bid}",
        "dur_s": float(buff.get("rem_ms", 7000)) / 1000.0,
        "is_contract_valid": False,
        "contract_warning": f"未在官方能力库中注册的 Buff ID: {bid}",
    }


# ---------------------------------------------------------------------------
# 2. C Simulator DLL Wrapper
# ---------------------------------------------------------------------------
class SimEngine:
    def __init__(self, dll_path):
        self.dll_path = dll_path
        self.dll = None
        self.load()

    def load(self):
        if not self.dll_path.exists():
            from build_sim import build
            build()
        self.dll = ctypes.CDLL(str(self.dll_path))
        self.setup_signatures()

    def setup_signatures(self):
        self.dll.sim_init.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float]
        self.dll.sim_init.restype = ctypes.c_int

        self.dll.sim_reset.argtypes = []
        self.dll.sim_reset.restype = None

        self.dll.sim_tick.argtypes = [ctypes.c_uint32]
        self.dll.sim_tick.restype = None

        self.dll.sim_attack.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]
        self.dll.sim_attack.restype = ctypes.c_int

        if hasattr(self.dll, 'sim_attack_start'):
            self.dll.sim_attack_start.argtypes = [ctypes.c_int, ctypes.c_int]
            self.dll.sim_attack_start.restype = ctypes.c_int

        self.dll.sim_set_block.argtypes = [ctypes.c_int, ctypes.c_int]
        self.dll.sim_set_block.restype = None

        self.dll.sim_dodge.argtypes = [ctypes.c_int, ctypes.c_int]
        self.dll.sim_dodge.restype = ctypes.c_int

        self.dll.sim_inject_buff.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_float, ctypes.c_int]
        self.dll.sim_inject_buff.restype = ctypes.c_int

        self.dll.sim_remove_buff.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
        self.dll.sim_remove_buff.restype = ctypes.c_int

        self.dll.sim_get_state_json.argtypes = [ctypes.c_char_p, ctypes.c_int]
        self.dll.sim_get_state_json.restype = ctypes.c_int

        self.dll.sim_pop_logs.argtypes = [ctypes.c_char_p, ctypes.c_int]
        self.dll.sim_pop_logs.restype = ctypes.c_int

        self.dll.sim_pop_floaters.argtypes = [ctypes.c_char_p, ctypes.c_int]
        self.dll.sim_pop_floaters.restype = ctypes.c_int

        if hasattr(self.dll, 'sim_set_mana'):
            self.dll.sim_set_mana.argtypes = [ctypes.c_int, ctypes.c_float]
            self.dll.sim_set_mana.restype = ctypes.c_int

        if hasattr(self.dll, 'sim_set_hp'):
            self.dll.sim_set_hp.argtypes = [ctypes.c_int, ctypes.c_float]
            self.dll.sim_set_hp.restype = ctypes.c_int

        if hasattr(self.dll, 'sim_set_crit_rate'):
            self.dll.sim_set_crit_rate.argtypes = [ctypes.c_int, ctypes.c_float]
            self.dll.sim_set_crit_rate.restype = ctypes.c_int

        if hasattr(self.dll, 'sim_set_special_attacking'):
            self.dll.sim_set_special_attacking.argtypes = [ctypes.c_int, ctypes.c_int]
            self.dll.sim_set_special_attacking.restype = ctypes.c_int

        if hasattr(self.dll, 'sim_set_heavy_attacking'):
            self.dll.sim_set_heavy_attacking.argtypes = [ctypes.c_int, ctypes.c_int]
            self.dll.sim_set_heavy_attacking.restype = ctypes.c_int

        if hasattr(self.dll, 'sim_dash'):
            self.dll.sim_dash.argtypes = [ctypes.c_int]
            self.dll.sim_dash.restype = ctypes.c_int

        if hasattr(self.dll, 'sim_get_projectile_speed'):
            self.dll.sim_get_projectile_speed.argtypes = [ctypes.c_int, ctypes.c_float, ctypes.c_int]
            self.dll.sim_get_projectile_speed.restype = ctypes.c_float

    def recompile(self):
        import _ctypes
        if self.dll:
            try:
                _ctypes.FreeLibrary(self.dll._handle)
            except Exception:
                pass
            self.dll = None

        import subprocess
        build_script = SIM_DIR / "build_sim.py"
        res = subprocess.run([sys.executable, str(build_script)], capture_output=True, text=True)
        if res.returncode == 0:
            self.load()
            return True, "Recompile succeeded!"
        return False, res.stderr or res.stdout

    def init(self, p0_bot, p1_bot, p0_hp, p1_hp, p0_atk, p1_atk):
        if "CURRENT_MATCHUP" in globals():
            CURRENT_MATCHUP["p0_bot_id"] = p0_bot
            CURRENT_MATCHUP["p1_bot_id"] = p1_bot
            CURRENT_MATCHUP["p0_hp"] = float(p0_hp)
            CURRENT_MATCHUP["p1_hp"] = float(p1_hp)
            CURRENT_MATCHUP["p0_atk"] = float(p0_atk)
            CURRENT_MATCHUP["p1_atk"] = float(p1_atk)
        return self.dll.sim_init(p0_bot.encode("utf-8"), p1_bot.encode("utf-8"),
                                 float(p0_hp), float(p1_hp), float(p0_atk), float(p1_atk))

    def reset(self):
        self.dll.sim_reset()

    def tick(self, dt_ms):
        self.dll.sim_tick(int(dt_ms))

    def attack_start(self, attacker, action_type):
        if hasattr(self.dll, 'sim_attack_start'):
            return self.dll.sim_attack_start(int(attacker), int(action_type))
        return 1

    def attack(self, attacker, action_type, hit_idx, is_last, is_blocked):
        return self.dll.sim_attack(int(attacker), int(action_type), int(hit_idx), int(is_last), int(is_blocked))

    def set_block(self, player, is_blocking):
        self.dll.sim_set_block(int(player), int(is_blocking))
        if is_blocking and "trigger_block_state_phase" in globals():
            trigger_block_state_phase(int(player), int(is_blocking))

    def set_mana(self, player, mana):
        if hasattr(self.dll, 'sim_set_mana'):
            return self.dll.sim_set_mana(int(player), ctypes.c_float(mana))
        return 0

    def set_hp(self, player, hp):
        if hasattr(self.dll, 'sim_set_hp'):
            return self.dll.sim_set_hp(int(player), ctypes.c_float(hp))
        return 0

    def set_crit_rate(self, player, crit_rate):
        if hasattr(self.dll, 'sim_set_crit_rate'):
            return self.dll.sim_set_crit_rate(int(player), ctypes.c_float(crit_rate))
        return 0

    def set_special_attacking(self, player, in_special):
        if hasattr(self.dll, 'sim_set_special_attacking'):
            return self.dll.sim_set_special_attacking(int(player), 1 if in_special else 0)
        return 0

    def set_heavy_attacking(self, player, is_heavy):
        if hasattr(self.dll, 'sim_set_heavy_attacking'):
            return self.dll.sim_set_heavy_attacking(int(player), 1 if is_heavy else 0)
        return 0

    def set_player_invincible(self, enabled):
        if hasattr(self.dll, 'sim_set_player_invincible'):
            return self.dll.sim_set_player_invincible(1 if enabled else 0)
        return 0

    def dodge(self, player, dodge_type):
        return self.dll.sim_dodge(int(player), int(dodge_type))

    def dash(self, player):
        if hasattr(self.dll, 'sim_dash'):
            return self.dll.sim_dash(int(player))
        return 1

    def get_projectile_speed(self, player: int, base_speed: float = 10.0, is_heavy: bool = False) -> float:
        if hasattr(self.dll, 'sim_get_projectile_speed'):
            return float(self.dll.sim_get_projectile_speed(int(player), ctypes.c_float(base_speed), 1 if is_heavy else 0))
        return base_speed

    def inject_buff(self, target, mod_id, dur, stacks):
        return self.dll.sim_inject_buff(int(target), mod_id.encode("utf-8"), float(dur), int(stacks))

    def remove_buff(self, target, mod_id, count):
        return self.dll.sim_remove_buff(int(target), mod_id.encode("utf-8"), int(count))

    def get_state(self):
        buf = ctypes.create_string_buffer(8192)
        self.dll.sim_get_state_json(buf, 8192)
        try:
            return json.loads(buf.value.decode("utf-8"))
        except Exception:
            return {"error": "JSON parse error", "raw": buf.value.decode("utf-8", "ignore")}

    def pop_logs(self):
        buf = ctypes.create_string_buffer(16384)
        self.dll.sim_pop_logs(buf, 16384)
        try:
            return json.loads(buf.value.decode("utf-8"))
        except Exception:
            return []

    def pop_floaters(self):
        buf = ctypes.create_string_buffer(8192)
        self.dll.sim_pop_floaters(buf, 8192)
        try:
            return json.loads(buf.value.decode("utf-8"))
        except Exception:
            return []

g_engine = SimEngine(DLL_PATH)

# 当前对战阵容与生命周期开局事件追踪
CURRENT_MATCHUP = {
    "p0_bot_id": "optimusprime_cin_tf",
    "p1_bot_id": "bonecrusher_cin_rotf",
    "p0_hp": 15000.0,
    "p1_hp": 15000.0,
    "p0_atk": 1000.0,
    "p1_atk": 1000.0,
}
PENDING_START_EVENTS = []

def resolve_bot_registry(bot_id: str):
    """支持完全匹配与前缀模糊解析 (例如 'megatron' 自动对齐 'megatron_gs_leader2015')。"""
    if not bot_id:
        return None
    if bot_id in _BOT_REGISTRY:
        return _BOT_REGISTRY[bot_id]
    for k, v in _BOT_REGISTRY.items():
        if bot_id in k or k in bot_id:
            return v
    return None

def trigger_onstart_phase():
    """
    IL2CPP 生命周期仿真引擎：0.00s 触发 onStart 技能。
    扫描双方角色的全部 StatMods，凡是含有 'onStart' 的修饰器，立即在第 0 秒注入并触发 Callout！
    这确保真机上的任何开局弹窗或开局被动，在模拟器上一模一样完全呈现！
    """
    global PENDING_START_EVENTS
    PENDING_START_EVENTS.clear()

    matchup = [
        (0, CURRENT_MATCHUP["p0_bot_id"], CURRENT_MATCHUP["p0_hp"], CURRENT_MATCHUP["p0_atk"]),
        (1, CURRENT_MATCHUP["p1_bot_id"], CURRENT_MATCHUP["p1_hp"], CURRENT_MATCHUP["p1_atk"]),
    ]

    for pidx, bid, base_hp, base_atk in matchup:
        reg = resolve_bot_registry(bid)
        if not reg:
            continue
        try:
            res = reg["builder"](base_hp=base_hp, base_atk=base_atk)
            mods = res[0] if isinstance(res, (tuple, list)) else res
            appears = res[1] if isinstance(res, (tuple, list)) and len(res) >= 2 else {}
        except Exception as e:
            print(f"[ERROR][onStart Phase] Builder error for {bid}: {e}")
            continue

        for mid, mod in mods.items():
            trs = mod.get("tr", [])
            uits = mod.get("uit", [])
            if "onStart" in trs or "onStart" in uits:
                ta = mod.get("ta", "self")
                target_idx = pidx if ta == "self" else (1 - pidx)
                dur = float(mod.get("d", -1.0))
                # 注入目标玩家
                g_engine.inject_buff(target_idx, mid, dur, 1)

                app_ids = mod.get("a", [])
                app = appears.get(app_ids[0], {}) if app_ids else {}
                callout = app.get("a") or app.get("st") or mid

                msg = f"[MATCH_START_TRIGGER] 0.00s 开局触发: P{pidx} ({bid}) 激活 '{mid}' -> 施加给 P{target_idx} (持续 {dur}s, 呼出: '{callout}')"
                print(msg)
                PENDING_START_EVENTS.append({
                    "pidx": target_idx,
                    "type": 4, # Callout floater
                    "val": 0,
                    "text": f"开局触发: {callout}",
                    "log": msg
                })

# 初始化默认阵容
g_engine.init(CURRENT_MATCHUP["p0_bot_id"], CURRENT_MATCHUP["p1_bot_id"],
              CURRENT_MATCHUP["p0_hp"], CURRENT_MATCHUP["p1_hp"],
              CURRENT_MATCHUP["p0_atk"], CURRENT_MATCHUP["p1_atk"])
trigger_onstart_phase()

def trigger_block_state_phase(pidx: int, is_blocking: int):
    """
    IL2CPP 生命周期仿真引擎：触发进入格挡状态机事件 (onPlayerStateEnter / state=Block)。
    当玩家切换为格挡 (is_blocking=1) 时，扫描角色的全部 StatMods，凡是含有 'onPlayerStateEnter' 
    且 trigger_scope 包含 'state=Block' 的修饰器，立即注入目标并触发 Callout！
    """
    if not is_blocking:
        return

    bid = CURRENT_MATCHUP["p0_bot_id"] if pidx == 0 else CURRENT_MATCHUP["p1_bot_id"]
    base_hp = CURRENT_MATCHUP["p0_hp"] if pidx == 0 else CURRENT_MATCHUP["p1_hp"]
    base_atk = CURRENT_MATCHUP["p0_atk"] if pidx == 0 else CURRENT_MATCHUP["p1_atk"]

    reg = resolve_bot_registry(bid)
    if not reg:
        return

    try:
        res = reg["builder"](base_hp=base_hp, base_atk=base_atk)
        mods = res[0] if isinstance(res, (tuple, list)) else res
        appears = res[1] if isinstance(res, (tuple, list)) and len(res) >= 2 else {}
    except Exception as e:
        print(f"[ERROR][Block Phase] Builder error for {bid}: {e}")
        return

    for mid, mod in mods.items():
        trs = mod.get("tr", [])
        uits = mod.get("uit", [])
        scope = mod.get("trs", "")
        # 只要监听 onPlayerStateEnter 且为 state=Block
        if ("onPlayerStateEnter" in trs or "onPlayerStateEnter" in uits) and ("state=Block" in scope or not scope):
            chance = float(mod.get("c", 1.0))
            if random.random() <= chance:
                ta = mod.get("ta", "self")
                target_idx = pidx if ta == "self" else (1 - pidx)
                dur = float(mod.get("d", -1.0))
                g_engine.inject_buff(target_idx, mid, dur, 1)

                app_ids = mod.get("a", [])
                app = appears.get(app_ids[0], {}) if app_ids else {}
                callout = app.get("a") or app.get("st") or mid

                msg = f"[BLOCK_ENTER_TRIGGER] 格挡姿态触发: P{pidx} ({bid}) 激活 '{mid}' -> 施加给 P{target_idx} (持续 {dur}s, 呼出: '{callout}')"
                print(msg)
                PENDING_START_EVENTS.append({
                    "pidx": target_idx,
                    "type": 4, # Callout floater
                    "val": 0,
                    "text": f"格挡触发: {callout}",
                    "log": msg
                })


# ---------------------------------------------------------------------------
# 3. 数据库与角色能力查询
# ---------------------------------------------------------------------------
def get_db_bots():
    if not DB_PATH.exists():
        return []
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT bot_id, name_zh, name_en, faction, class, hp, attack, rating FROM characters ORDER BY name_zh").fetchall()
    bots = [dict(r) for r in rows]
    conn.close()
    return bots

def get_bot_abilities(bot_id):
    if not DB_PATH.exists():
        return {"bot": None, "implemented_skills": [], "db_abilities": []}
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    # 1. 查找角色基础资料
    char_row = conn.execute("SELECT bot_id, name_zh, name_en, faction, class, hp, attack, rating FROM characters WHERE bot_id = ?", (bot_id,)).fetchone()
    bot_info = dict(char_row) if char_row else {"bot_id": bot_id, "name_zh": bot_id, "name_en": bot_id}

    # 2. 查找官方技能库
    rows = conn.execute("SELECT id, category, title_zh, title_en, desc_zh, pua_icon FROM character_abilities WHERE bot_id = ? ORDER BY sort_order", (bot_id,)).fetchall()
    db_abilities = []
    for r in rows:
        d = dict(r)
        if not d.get("pua_icon"):
            d["pua_icon"] = guess_pua(d.get("title_zh"), d.get("desc_zh"))
        db_abilities.append(d)
    conn.close()

    # 3. 从 Server/abilities/ 官方注册表提取全部契约修饰器
    implemented = []
    reg = resolve_bot_registry(bot_id)
    if reg:
        try:
            res = reg["builder"](base_hp=30000.0, base_atk=3000.0)
            mods = res[0] if isinstance(res, (tuple, list)) else res
            appears = res[1] if isinstance(res, (tuple, list)) and len(res) >= 2 else {}
            for mid, m in mods.items():
                app_ids = m.get("a", [])
                app = appears.get(app_ids[0], {}) if app_ids else {}
                pua_char = app.get("t", "")
                pua_hex = ("0x" + hex(ord(pua_char))[2:].upper()) if pua_char else "0xE406"
                title = app.get("a") or app.get("s") or mid
                desc = app.get("l") or app.get("pl") or f"触发条件: {m.get('tr', [])}"
                category = "被动能力" if "always" in m.get("tr", []) else "触发修饰器"
                if "Special1" in str(m.get("trs", "")) or "Special1" in str(m.get("tr", "")):
                    category = "特殊技1"
                elif "Special2" in str(m.get("trs", "")) or "Special2" in str(m.get("tr", "")):
                    category = "特殊技2"
                elif "Special3" in str(m.get("trs", "")) or "Special3" in str(m.get("tr", "")):
                    category = "特殊技3"

                implemented.append({
                    "title": title,
                    "category": category,
                    "pua_icon": pua_hex,
                    "desc": desc,
                    "status": "Server/abilities 契约已载入",
                    "triggers": m.get("tr", []),
                    "duration": m.get("d", 0.0),
                    "target": m.get("ta", "self"),
                    "color_tc": app.get("tc", "FFFFFF"),
                    "color_gb": app.get("gb", "888888"),
                })
        except Exception as e:
            print(f"[WARN] Failed to load registry skills for {bot_id}: {e}")

    # 若未在能力注册表中，从 SQLite 官方技能库补全
    if not implemented and db_abilities:
        for a in db_abilities:
            if a.get("category") in ("passive", "signature", "sp1", "sp2", "sp3", "被动", "特殊技"):
                implemented.append({
                    "title": a.get("title_zh", ""),
                    "category": a.get("category", "被动"),
                    "pua_icon": a.get("pua_icon") or guess_pua(a.get("title_zh"), a.get("desc_zh")),
                    "desc": a.get("desc_zh", ""),
                    "status": "官方机制已载入"
                })

    return {
        "bot": bot_info,
        "has_c_module": len(implemented) > 0,
        "implemented_skills": implemented,
        "db_abilities": db_abilities
    }

# ---------------------------------------------------------------------------
# 4. HTTP Request Handler
# ---------------------------------------------------------------------------
class SimHTTPHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/bots":
            self.send_json(get_db_bots())
        elif parsed.path.startswith("/api/bot/"):
            bot_id = parsed.path.split("/")[-1]
            self.send_json(get_bot_abilities(bot_id))
        elif parsed.path == "/api/state":
            st = g_engine.get_state()
            logs = g_engine.pop_logs()
            floaters = g_engine.pop_floaters()

            # 注入开局生命周期事件
            global PENDING_START_EVENTS
            if PENDING_START_EVENTS:
                for evt in PENDING_START_EVENTS:
                    floaters.append({"pidx": evt["pidx"], "type": evt["type"], "val": evt["val"], "text": evt["text"]})
                    logs.append(evt["log"])
                PENDING_START_EVENTS.clear()

            # 数据契约装饰与校验
            if "p0" in st and "buffs" in st["p0"]:
                st["p0"]["buffs"] = [decorate_buff(b) for b in st["p0"]["buffs"]]
            if "p1" in st and "buffs" in st["p1"]:
                st["p1"]["buffs"] = [decorate_buff(b) for b in st["p1"]["buffs"]]

            st["logs"] = logs
            st["floaters"] = floaters
            self.send_json(st)
        else:
            super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
        try:
            data = json.loads(body)
        except Exception:
            data = {}

        if parsed.path == "/api/init":
            p0 = data.get("p0_bot_id", "optimusprime_cin_tf")
            p1 = data.get("p1_bot_id", "bonecrusher_cin_rotf")
            p0_hp = data.get("p0_hp", 15000.0)
            p1_hp = data.get("p1_hp", 15000.0)
            p0_atk = data.get("p0_atk", 1000.0)
            p1_atk = data.get("p1_atk", 1000.0)

            CURRENT_MATCHUP["p0_bot_id"] = p0
            CURRENT_MATCHUP["p1_bot_id"] = p1
            CURRENT_MATCHUP["p0_hp"] = p0_hp
            CURRENT_MATCHUP["p1_hp"] = p1_hp
            CURRENT_MATCHUP["p0_atk"] = p0_atk
            CURRENT_MATCHUP["p1_atk"] = p1_atk

            g_engine.init(p0, p1, p0_hp, p1_hp, p0_atk, p1_atk)
            trigger_onstart_phase()
            self.send_json({"ok": True})

        elif parsed.path == "/api/reset":
            g_engine.reset()
            trigger_onstart_phase()
            self.send_json({"ok": True})

        elif parsed.path == "/api/tick":
            dt = data.get("dt_ms", 100)
            g_engine.tick(dt)
            self.send_json({"ok": True})

        elif parsed.path == "/api/attack_start":
            attacker = int(data.get("attacker", 0))
            action = int(data.get("action", 4))
            ok = g_engine.attack_start(attacker, action)
            self.send_json({"ok": bool(ok)})

        elif parsed.path == "/api/set_special":
            player = int(data.get("player", 0))
            in_special = bool(data.get("in_special", True))
            ok = g_engine.set_special_attacking(player, in_special)
            self.send_json({"ok": bool(ok)})

        elif parsed.path == "/api/set_heavy":
            player = int(data.get("player", 0))
            is_heavy = bool(data.get("is_heavy", True))
            ok = g_engine.set_heavy_attacking(player, is_heavy)
            self.send_json({"ok": bool(ok)})

        elif parsed.path == "/api/player_invincible":
            enabled = bool(data.get("enabled", True))
            ok = g_engine.set_player_invincible(enabled)
            self.send_json({"ok": bool(ok), "invincible": enabled})

        elif parsed.path == "/api/attack":
            attacker = data.get("attacker", 0)
            action = data.get("action", 1) # 1=L, 2=M, 4=Heavy, 16=SP1, 32=SP2, 64=SP3
            hit_idx = data.get("hit_idx", 0)
            is_last = data.get("is_last", 1)
            blocked = data.get("blocked", 0)
            dmg = g_engine.attack(attacker, action, hit_idx, is_last, blocked)
            self.send_json({"ok": True, "dmg": dmg})

        elif parsed.path == "/api/block":
            player = data.get("player", 0)
            blocking = data.get("blocking", 1)
            g_engine.set_block(player, blocking)
            self.send_json({"ok": True})

        elif parsed.path == "/api/dodge":
            player = data.get("player", 0)
            dodge_type = data.get("type", 0) # 0=Dash Back, 1=Sidestep
            ok = g_engine.dodge(player, dodge_type)
            self.send_json({"ok": bool(ok)})

        elif parsed.path == "/api/inject_buff":
            target = data.get("target", 0)
            mod_id = data.get("mod_id", "dmg_bleed")
            dur = data.get("dur", 6.0)
            stacks = data.get("stacks", 1)
            g_engine.inject_buff(target, mod_id, dur, stacks)
            self.send_json({"ok": True})

        elif parsed.path == "/api/remove_buff":
            target = data.get("target", 0)
            mod_id = data.get("mod_id", "")
            count = data.get("count", 1)
            g_engine.remove_buff(target, mod_id, count)
            self.send_json({"ok": True})

        elif parsed.path == "/api/mana":
            player = int(data.get("player", 0))
            mana = float(data.get("mana", 1.0))
            g_engine.set_mana(player, mana)
            self.send_json({"ok": True, "player": player, "mana": mana})

        elif parsed.path == "/api/recompile":
            ok, msg = g_engine.recompile()
            self.send_json({"ok": ok, "message": msg})
        else:
            self.send_response(404)
            self.end_headers()

    def send_json(self, obj):
        content = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(content)

def run_server(port=8088):
    server = HTTPServer(("0.0.0.0", port), SimHTTPHandler)
    url = f"http://localhost:{port}/index.html"
    print(f"\n" + "=" * 70)
    print(f"🚀 TFTF 战斗技能沙盒模拟器 (契约与生命周期增强版) 已就绪!")
    print(f"👉 访问地址: {url}")
    print(f"=" * 70 + "\n")
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] 服务器已关闭。")

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8088
    run_server(port)
