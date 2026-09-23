import http.server
import socketserver
import json
import sqlite3
import os
import sys
import urllib.parse
from pathlib import Path

PORT = 8888
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "Server" / "tftf_database.db"
WEB_DIR = BASE_DIR / "tools" / "web_dashboard"

sys.path.append(str(BASE_DIR / "Server"))
import gamedata

def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def resolve_portrait_file(bid):
    base = gamedata.art_base(bid)
    candidates = [
        BASE_DIR / f"assets_redeco/portrait_{base}_small.jpg",
        BASE_DIR / f"assets_redeco/portrait_{base}_small.png",
        BASE_DIR / f"assets_netflix/portrait_{base}_small.jpg",
        BASE_DIR / f"assets_netflix/portrait_{base}_small.png",
        BASE_DIR / f"extracted_apk/assets/assetpack/portraits_odr/portraits/portrait_{base}_small.jpg",
        BASE_DIR / f"extracted_apk/assets/assetpack/portraits_odr/portraits/portrait_{base}_small.png",
        BASE_DIR / f"assets_redeco/portrait_{bid}_small.jpg",
        BASE_DIR / f"assets_redeco/portrait_{bid}_small.png",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None

class DashboardHandler(http.server.BaseHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def serve_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        path = url.path

        # 1. Static Web Dashboard
        if path in ("/", "/index.html"):
            index_path = WEB_DIR / "index.html"
            if index_path.exists():
                data = index_path.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
            else:
                self.send_error(404, "index.html not found")
                return

        # 2. Font File
        elif path == "/fonts/Tecnica_Bold_116.ttf":
            font_path = WEB_DIR / "Tecnica_Bold_116.ttf"
            if font_path.exists():
                data = font_path.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "font/ttf")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
            else:
                self.send_error(404, "Font not found")
                return

        # 3. Portrait Endpoint: /portrait/<bid>
        elif path.startswith("/portrait/"):
            bid = path[len("/portrait/"):]
            p_file = resolve_portrait_file(bid)
            if p_file and p_file.exists():
                data = p_file.read_bytes()
                mime = "image/png" if p_file.suffix.lower() == ".png" else "image/jpeg"
                self.send_response(200)
                self.send_header("Content-Type", mime)
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Cache-Control", "public, max-age=86400")
                self.end_headers()
                self.wfile.write(data)
                return
            else:
                # Return empty 1x1 transparent png or 404
                self.send_error(404, "Portrait not found")
                return

        # 4. API: /api/overview
        elif path == "/api/overview":
            conn = get_db()
            c = conn.cursor()

            # Classes
            classes = [dict(r) for r in c.execute("SELECT * FROM class_defaults ORDER BY sort_order, class_id").fetchall()]
            class_map = {cl["class_id"]: cl for cl in classes}

            # Factions
            factions = [dict(r) for r in c.execute("SELECT * FROM factions ORDER BY faction_id").fetchall()]

            # Characters ordered by: class, source (Kabam regular -> Kabam Sharkticon -> Netflix -> Revival), then bot_id
            chars_rows = c.execute("""
                SELECT * FROM characters
                ORDER BY class,
                         CASE
                             WHEN source = 'Kabam' AND bot_id NOT LIKE '%shark%' THEN 0
                             WHEN source = 'Kabam' AND bot_id LIKE '%shark%' THEN 1
                             WHEN source = 'Netflix' THEN 2
                             WHEN source = 'Revival' THEN 3
                             ELSE 4
                         END,
                         bot_id
            """).fetchall()
            characters = []
            for r in chars_rows:
                cd = dict(r)
                klass = cd["class"]
                c_def = class_map.get(klass, {})
                # Effective crit rate
                eff_crit = cd["crit_chance"] if cd["crit_chance"] is not None else c_def.get("crit_chance", 0.15)
                eff_crit_dmg = cd["crit_damage"] if cd["crit_damage"] is not None else c_def.get("crit_damage", 1.5)
                eff_ranged = cd["crit_chance_ranged"] if cd["crit_chance_ranged"] is not None else (eff_crit + c_def.get("ranged_crit_bonus", 0.0))
                eff_melee = cd["crit_chance_melee"] if cd["crit_chance_melee"] is not None else eff_crit
                cd["effective_crit_chance"] = eff_crit
                cd["effective_crit_damage"] = eff_crit_dmg
                cd["effective_crit_ranged"] = eff_ranged
                cd["effective_crit_melee"] = eff_melee
                cd["portrait_url"] = f"/portrait/{cd['bot_id']}"
                characters.append(cd)

            total_abilities = c.execute("SELECT COUNT(*) FROM character_abilities").fetchone()[0]
            conn.close()
            self.serve_json({
                "classes": classes,
                "factions": factions,
                "characters": characters,
                "total_abilities": total_abilities,
            })
            return

        # 5. API: /api/character/<bid>
        elif path.startswith("/api/character/"):
            bid = path[len("/api/character/"):]
            conn = get_db()
            c = conn.cursor()
            char_row = c.execute("SELECT * FROM characters WHERE bot_id = ?", (bid,)).fetchone()
            if not char_row:
                conn.close()
                self.serve_json({"error": "Character not found"}, status=404)
                return

            cd = dict(char_row)
            cd["portrait_url"] = f"/portrait/{bid}"

            # Abilities
            ab_rows = c.execute("SELECT * FROM character_abilities WHERE bot_id = ? ORDER BY sort_order, id", (bid,)).fetchall()
            abilities = []
            for r in ab_rows:
                ad = dict(r)
                if "synergy_bots" in ad and ad["synergy_bots"]:
                    try:
                        ad["synergy_bots"] = json.loads(ad["synergy_bots"])
                    except Exception:
                        ad["synergy_bots"] = []
                else:
                    ad["synergy_bots"] = []
                abilities.append(ad)
            cd["abilities"] = abilities

            conn.close()
            self.serve_json(cd)
            return

        # 6. API: /api/pua_icons
        elif path == "/api/pua_icons":
            conn = get_db()
            c = conn.cursor()
            icons = [dict(r) for r in c.execute("SELECT * FROM pua_icons_cache ORDER BY codepoint_dec").fetchall()]
            conn.close()
            self.serve_json({"icons": icons})
            return

        self.send_error(404, "Not Found")

    def do_POST(self):
        url = urllib.parse.urlparse(self.path)
        path = url.path
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length > 0 else b"{}"
        try:
            payload = json.loads(body.decode("utf-8"))
        except Exception:
            payload = {}

        # 1. Update Character: /api/character/<bid>
        if path.startswith("/api/character/"):
            bid = path[len("/api/character/"):]
            conn = get_db()
            c = conn.cursor()

            updatable = [
                "crit_chance", "crit_damage", "crit_chance_ranged", "crit_chance_melee",
                "health_mult", "attack_mult", "block_proficiency", "mana_gain_mult",
                "pua_faction_icon", "pua_class_icon", "desc_zh", "note", "class", "faction", "source"
            ]
            fields = []
            values = []
            for k in updatable:
                if k in payload:
                    val = payload[k]
                    # Convert empty strings to None for numeric fields
                    if val == "" and k in ["crit_chance", "crit_damage", "crit_chance_ranged", "crit_chance_melee"]:
                        val = None
                    fields.append(f"{k} = ?")
                    values.append(val)

            if fields:
                values.append(bid)
                sql = f"UPDATE characters SET {', '.join(fields)}, updated_at = CURRENT_TIMESTAMP WHERE bot_id = ?"
                c.execute(sql, values)
                conn.commit()

            conn.close()
            self.serve_json({"ok": True, "bot_id": bid})
            return

        # 2. Add New Ability: /api/ability/new
        elif path == "/api/ability/new":
            conn = get_db()
            c = conn.cursor()
            bot_id = payload.get("bot_id")
            category = payload.get("category", "passive")
            title_zh = payload.get("title_zh", "新技能")
            title_en = payload.get("title_en", "")
            desc_zh = payload.get("desc_zh", "")
            desc_en = payload.get("desc_en", "")
            pua_icon = payload.get("pua_icon", "")
            synergy_bots = payload.get("synergy_bots", [])
            if isinstance(synergy_bots, list):
                synergy_bots_str = json.dumps(synergy_bots)
            else:
                synergy_bots_str = str(synergy_bots)

            c.execute("""
                INSERT INTO character_abilities (bot_id, category, title_zh, title_en, desc_zh, desc_en, pua_icon, synergy_bots, sort_order)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (bot_id, category, title_zh, title_en, desc_zh, desc_en, pua_icon, synergy_bots_str, 0))
            conn.commit()
            new_id = c.lastrowid
            conn.close()
            self.serve_json({"ok": True, "id": new_id})
            return

        # 2.1 Delete Ability: /api/ability/delete/<id>
        elif path.startswith("/api/ability/delete/"):
            aid = path[len("/api/ability/delete/"):]
            conn = get_db()
            c = conn.cursor()
            c.execute("DELETE FROM character_abilities WHERE id = ?", (aid,))
            conn.commit()
            conn.close()
            self.serve_json({"ok": True, "deleted_id": aid})
            return

        # 2.2 Update Ability: /api/ability/<id>
        elif path.startswith("/api/ability/"):
            aid = path[len("/api/ability/"):]
            conn = get_db()
            c = conn.cursor()

            fields = []
            values = []
            for k in ["pua_icon", "title_zh", "title_en", "desc_zh", "desc_en"]:
                if k in payload:
                    fields.append(f"{k} = ?")
                    values.append(payload[k])

            if "synergy_bots" in payload:
                s_bots = payload["synergy_bots"]
                s_str = json.dumps(s_bots) if isinstance(s_bots, list) else str(s_bots)
                fields.append("synergy_bots = ?")
                values.append(s_str)

            if fields:
                values.append(aid)
                sql = f"UPDATE character_abilities SET {', '.join(fields)} WHERE id = ?"
                c.execute(sql, values)
                conn.commit()

            conn.close()
            self.serve_json({"ok": True, "id": aid})
            return

        # 3. Update Class: /api/class/<class_id>
        elif path.startswith("/api/class/"):
            cid = path[len("/api/class/"):]
            conn = get_db()
            c = conn.cursor()

            fields = []
            values = []
            for k in ["pua_icon", "crit_chance", "crit_damage", "ranged_crit_bonus", "trait_zh"]:
                if k in payload:
                    fields.append(f"{k} = ?")
                    values.append(payload[k])

            if fields:
                values.append(cid)
                sql = f"UPDATE class_defaults SET {', '.join(fields)} WHERE class_id = ?"
                c.execute(sql, values)
                conn.commit()

            conn.close()
            self.serve_json({"ok": True, "class_id": cid})
            return

        # 4. Update Faction: /api/faction/<faction_id>
        elif path.startswith("/api/faction/"):
            fid = path[len("/api/faction/"):]
            conn = get_db()
            c = conn.cursor()

            fields = []
            values = []
            for k in ["pua_icon"]:
                if k in payload:
                    fields.append(f"{k} = ?")
                    values.append(payload[k])

            if fields:
                values.append(fid)
                sql = f"UPDATE factions SET {', '.join(fields)} WHERE faction_id = ?"
                c.execute(sql, values)
                conn.commit()

            conn.close()
            self.serve_json({"ok": True, "faction_id": fid})
            return

        self.send_error(404, "Not Found")

def run_server(port=PORT):
    server_address = ("127.0.0.1", port)
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(server_address, DashboardHandler) as httpd:
        print(f"\n========================================================")
        print(f"  TFTF Character & Ability Visual Dashboard")
        print(f"  Local Web Address: http://127.0.0.1:{port}")
        print(f"========================================================\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")

if __name__ == "__main__":
    run_server()
