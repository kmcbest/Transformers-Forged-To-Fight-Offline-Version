#!/usr/bin/env python3
"""
Sync TFTF Web Dashboard and Database to GitHub Pages / Vercel Repository
Target repo: D:/docforall/GitHub/kmcbest.github.io/tftfr
"""

import os
import sys
import json
import sqlite3
import re
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TFTF_DB = REPO_ROOT / "Server" / "tftf_database.db"
LOCAL_INDEX = REPO_ROOT / "tools" / "web_dashboard" / "index.html"

TARGET_DIR = Path(r"D:\docforall\GitHub\kmcbest.github.io\tftfr")
TARGET_DATA_DIR = TARGET_DIR / "data"
TARGET_CHARS_DIR = TARGET_DATA_DIR / "characters"
TARGET_BOTS_HTML = TARGET_DIR / "bots.html"

UPSTASH_URL = "https://deciding-bulldog-136761.upstash.io"
UPSTASH_TOKEN = "gQAAAAAAAhY5AAIgcDEyZGMwZDRhNzRlZGQ0MDI2YWM2YmI3ZDExNTc3ZjZmNA"


def sync_database_data():
    print(f"[*] Reading SQLite Database: {TFTF_DB}")
    conn = sqlite3.connect(str(TFTF_DB))
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    classes = [dict(r) for r in c.execute("SELECT * FROM class_defaults ORDER BY sort_order, class_id").fetchall()]
    class_map = {cl["class_id"]: cl for cl in classes}

    factions = [dict(r) for r in c.execute("SELECT * FROM factions ORDER BY faction_id").fetchall()]

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
        eff_crit = cd["crit_chance"] if cd["crit_chance"] is not None else c_def.get("crit_chance", 0.15)
        eff_crit_dmg = cd["crit_damage"] if cd["crit_damage"] is not None else c_def.get("crit_damage", 1.5)
        eff_ranged = cd["crit_chance_ranged"] if cd["crit_chance_ranged"] is not None else (eff_crit + c_def.get("ranged_crit_bonus", 0.0))
        eff_melee = cd["crit_chance_melee"] if cd["crit_chance_melee"] is not None else eff_crit
        cd["effective_crit_chance"] = eff_crit
        cd["effective_crit_damage"] = eff_crit_dmg
        cd["effective_crit_ranged"] = eff_ranged
        cd["effective_crit_melee"] = eff_melee
        cd["portrait_url"] = f"portraits/{cd['bot_id']}.png"
        cd["portrait_large_url"] = f"portraits/{cd['bot_id']}_large.png"
        characters.append(cd)

    total_abilities = c.execute("SELECT COUNT(*) FROM character_abilities").fetchone()[0]

    overview_data = {
        "classes": classes,
        "factions": factions,
        "characters": characters,
        "total_abilities": total_abilities,
    }

    TARGET_DATA_DIR.mkdir(parents=True, exist_ok=True)
    TARGET_CHARS_DIR.mkdir(parents=True, exist_ok=True)

    overview_file = TARGET_DATA_DIR / "overview.json"
    with open(overview_file, "w", encoding="utf-8") as f:
        json.dump(overview_data, f, ensure_ascii=False, indent=2)
    print(f"    [+] Wrote {overview_file} ({len(characters)} characters, {total_abilities} abilities)")

    all_bots_dict = {}
    for cd in characters:
        bid = cd["bot_id"]
        ab_rows = c.execute("SELECT * FROM character_abilities WHERE bot_id = ? ORDER BY sort_order, id", (bid,)).fetchall()
        abilities = []
        for ar in ab_rows:
            ad = dict(ar)
            if ad.get("synergy_bots"):
                try:
                    ad["synergy_bots"] = json.loads(ad["synergy_bots"])
                except Exception:
                    ad["synergy_bots"] = []
            else:
                ad["synergy_bots"] = []
            abilities.append(ad)

        char_detail = dict(cd)
        char_detail["abilities"] = abilities

        char_file = TARGET_CHARS_DIR / f"{bid}.json"
        with open(char_file, "w", encoding="utf-8") as f:
            json.dump(char_detail, f, ensure_ascii=False, indent=2)

        all_bots_dict[bid] = char_detail

    all_abilities_file = TARGET_DATA_DIR / "all_abilities.json"
    with open(all_abilities_file, "w", encoding="utf-8") as f:
        json.dump({
            "total_bots": len(all_bots_dict),
            "total_abilities": total_abilities,
            "bots": all_bots_dict
        }, f, ensure_ascii=False, indent=2)
    print(f"    [+] Wrote {all_abilities_file} ({len(all_bots_dict)} bots bundled)")

    conn.close()
    return overview_data, all_bots_dict


def update_bots_html():
    print(f"[*] Adapting {LOCAL_INDEX} into {TARGET_BOTS_HTML}...")
    with open(LOCAL_INDEX, "r", encoding="utf-8") as f:
        html = f.read()

    # 1. Update font-face URL for GitHub Pages / Vercel
    html = html.replace(
        "src: url('/fonts/Tecnica_Bold_116.ttf') format('truetype');",
        "src: url('./fonts/Tecnica_Bold_116.ttf'), url('./Tecnica_Bold_116.ttf') format('truetype');"
    )

    # 2. Update Header Badge
    html = html.replace(
        '<span class="logo-badge">SQLite Local Live</span>',
        '<span class="logo-badge">Upstash KV Live</span>'
    )

    # 3. Replace the Script tag data source logic
    # In index.html, it starts with let gOverviewData = null; and calls fetch('/api/overview')
    # We replace the data-fetching and saving section with Upstash KV client and fallback logic.

    upstash_client_block = """
        // ==========================================
        // Upstash KV Online Storage Client & Fallback
        // ==========================================
        const UPSTASH = {
            url: "https://deciding-bulldog-136761.upstash.io",
            token: "gQAAAAAAAhY5AAIgcDEyZGMwZDRhNzRlZGQ0MDI2YWM2YmI3ZDExNTc3ZjZmNA",
            readToken: "ggAAAAAAAhY5AAIgcDG7a511dMnvUap5JjML7kdCMH0hQAG95-3BtwD6YEaFeQ"
        };

        async function kvGet(key, fallbackPath) {
            try {
                const res = await fetch(`${UPSTASH.url}/get/${encodeURIComponent(key)}`, {
                    headers: { 'Authorization': `Bearer ${UPSTASH.readToken}` }
                });
                if (res.ok) {
                    const json = await res.json();
                    if (json && json.result) {
                        return typeof json.result === 'string' ? JSON.parse(json.result) : json.result;
                    }
                }
            } catch (err) {
                console.warn(`Upstash KV read failed for [${key}], falling back:`, err);
            }
            if (fallbackPath) {
                try {
                    const fbRes = await fetch(fallbackPath);
                    if (fbRes.ok) return await fbRes.json();
                } catch (fbErr) {
                    console.error(`Fallback fetch failed for [${fallbackPath}]:`, fbErr);
                }
            }
            return null;
        }

        async function kvSet(key, value) {
            try {
                const res = await fetch(`${UPSTASH.url}/set/${encodeURIComponent(key)}`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${UPSTASH.token}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(value)
                });
                const json = await res.json();
                return json && json.result === 'OK';
            } catch (err) {
                console.error(`Upstash KV write failed for [${key}]:`, err);
                return false;
            }
        }
    """

    # Inject upstash client right after <script>
    html = html.replace("<script>", "<script>\n" + upstash_client_block)

    with open(TARGET_BOTS_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"    [+] Successfully updated {TARGET_BOTS_HTML} ({len(html)} bytes)")


def sync_to_upstash_kv(overview_data, all_bots_dict):
    print("[*] Synchronizing latest SQLite database into Upstash KV...")
    try:
        # Sync overview
        req = urllib.request.Request(
            f"{UPSTASH_URL}/set/tftf:overview",
            data=json.dumps(overview_data).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {UPSTASH_TOKEN}",
                "Content-Type": "application/json"
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            ret = json.loads(resp.read().decode("utf-8"))
            print(f"    [+] Synced tftf:overview -> {ret.get('result')}")

        # Sync characters
        success_count = 0
        for bid, char_detail in all_bots_dict.items():
            req = urllib.request.Request(
                f"{UPSTASH_URL}/set/tftf:char:{bid}",
                data=json.dumps(char_detail).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {UPSTASH_TOKEN}",
                    "Content-Type": "application/json"
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                success_count += 1
        print(f"    [+] Successfully synced {success_count} characters to Upstash KV!")
    except Exception as e:
        print(f"    [!] Upstash KV sync error (non-fatal, static CDN fallback is ready): {e}")


def main():
    overview_data, all_bots_dict = sync_database_data()
    update_bots_html()
    sync_to_upstash_kv(overview_data, all_bots_dict)
    print("\n[OK] All web dashboard data and bots.html synchronized successfully!")


if __name__ == "__main__":
    main()
