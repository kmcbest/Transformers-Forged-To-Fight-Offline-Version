#!/usr/bin/env python3
"""
TFTF Desktop Combat Simulator Server
===================================
Local HTTP Server providing Web UI and REST API for the Combat Sandbox.
"""
import os
import sys
import json
import sqlite3
import ctypes
import webbrowser
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SIM_DIR = REPO_ROOT / "tools/sim"
WEB_DIR = SIM_DIR / "web"
DB_PATH = REPO_ROOT / "Server/tftf_database.db"
DLL_PATH = SIM_DIR / "sim_skills.dll"

# ---------------------------------------------------------------------------
# C Simulator DLL Wrapper
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

    def recompile(self):
        # On Windows, unload the DLL by freeing library handle before overwriting
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
        return self.dll.sim_init(p0_bot.encode("utf-8"), p1_bot.encode("utf-8"),
                                 float(p0_hp), float(p1_hp), float(p0_atk), float(p1_atk))

    def reset(self):
        self.dll.sim_reset()

    def tick(self, dt_ms):
        self.dll.sim_tick(int(dt_ms))

    def attack(self, attacker, action_type, hit_idx, is_last, is_blocked):
        return self.dll.sim_attack(int(attacker), int(action_type), int(hit_idx), int(is_last), int(is_blocked))

    def set_block(self, player, is_blocking):
        self.dll.sim_set_block(int(player), int(is_blocking))

    def dodge(self, player, dodge_type):
        return self.dll.sim_dodge(int(player), int(dodge_type))

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

# Initialize with default matchup
g_engine.init("optimusprime_cin_tf", "bonecrusher_cin_rotf", 15000.0, 15000.0, 1000.0, 1000.0)

# ---------------------------------------------------------------------------
# Database Helper
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
        return []
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT id, category, title_zh, title_en, desc_zh, pua_icon FROM character_abilities WHERE bot_id = ? ORDER BY sort_order", (bot_id,)).fetchall()
    abilities = [dict(r) for r in rows]
    conn.close()
    return abilities

# ---------------------------------------------------------------------------
# HTTP Request Handler
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
            st["logs"] = g_engine.pop_logs()
            st["floaters"] = g_engine.pop_floaters()
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
            g_engine.init(p0, p1, p0_hp, p1_hp, p0_atk, p1_atk)
            self.send_json({"ok": True})

        elif parsed.path == "/api/reset":
            g_engine.reset()
            self.send_json({"ok": True})

        elif parsed.path == "/api/tick":
            dt = data.get("dt_ms", 100)
            g_engine.tick(dt)
            self.send_json({"ok": True})

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
    print(f"🚀 TFTF 战斗技能沙盒模拟器已就绪!")
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
