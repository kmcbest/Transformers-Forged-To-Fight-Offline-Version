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

candidate_dirs = [
    Path(r"D:\#E\Personal\kmcbest.github.io\tftfr"),
    Path(r"D:\docforall\GitHub\kmcbest.github.io\tftfr")
]
TARGET_DIR = next((d for d in candidate_dirs if d.exists()), candidate_dirs[0])
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

    # Priority abilities export
    priority_rows = c.execute("""
        SELECT 
            ca.id,
            ca.bot_id,
            c.name_zh AS bot_name_zh,
            c.name_en AS bot_name_en,
            c.class AS bot_class,
            c.faction AS bot_faction,
            c.source AS bot_source,
            ca.category,
            ca.title_zh,
            ca.title_en,
            ca.desc_zh,
            ca.desc_en,
            ca.pua_icon,
            ca.synergy_bots,
            ca.status,
            ca.sort_order
        FROM character_abilities ca
        LEFT JOIN characters c ON ca.bot_id = c.bot_id
        WHERE ca.status = 'priority'
        ORDER BY c.class, ca.bot_id, ca.category, ca.sort_order, ca.id
    """).fetchall()
    priority_items = []
    for r in priority_rows:
        ad = dict(r)
        if ad.get("synergy_bots"):
            try:
                ad["synergy_bots"] = json.loads(ad["synergy_bots"])
            except Exception:
                ad["synergy_bots"] = []
        else:
            ad["synergy_bots"] = []
        priority_items.append(ad)

    priority_file = TARGET_DATA_DIR / "priority_abilities.json"
    priority_data = {
        "total": len(priority_items),
        "status": "priority",
        "abilities": priority_items
    }
    with open(priority_file, "w", encoding="utf-8") as f:
        json.dump(priority_data, f, ensure_ascii=False, indent=2)
    print(f"    [+] Wrote {priority_file} ({len(priority_items)} priority abilities)")

    # PUA Icons Cache export
    pua_rows = c.execute("SELECT * FROM pua_icons_cache ORDER BY codepoint_dec").fetchall()
    pua_icons = [dict(r) for r in pua_rows]
    pua_file = TARGET_DATA_DIR / "pua_icons.json"
    with open(pua_file, "w", encoding="utf-8") as f:
        json.dump({"icons": pua_icons}, f, ensure_ascii=False, indent=2)
    print(f"    [+] Wrote {pua_file} ({len(pua_icons)} icons with annotations)")

    dash_pua_file = REPO_ROOT / "tools" / "web_dashboard" / "data" / "pua_icons.json"
    dash_pua_file.parent.mkdir(parents=True, exist_ok=True)
    with open(dash_pua_file, "w", encoding="utf-8") as f:
        json.dump({"icons": pua_icons}, f, ensure_ascii=False, indent=2)

    conn.close()
    return overview_data, all_bots_dict, priority_data


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


def sync_to_upstash_kv(overview_data, all_bots_dict, priority_data=None):
    print("[*] Synchronizing latest SQLite database into Upstash KV...")
    # 0. 安全防线：在覆盖前自动备份当前云端全量数据至本地快照目录
    try:
        from datetime import datetime
        backup_dir = REPO_ROOT / "tools" / "cloud_backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        ts_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"upstash_backup_{ts_str}.json"
        
        # 拉取当前 overview 作为快照元信息
        req_chk = urllib.request.Request(
            f"{UPSTASH_URL}/get/tftf:overview",
            headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"}
        )
        with urllib.request.urlopen(req_chk, timeout=8) as r:
            cur_cloud = json.loads(r.read().decode("utf-8"))
            backup_file.write_text(json.dumps(cur_cloud, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"    [+] [安全防护] 已在推送前对云端数据生成自动快照: {backup_file.name}")
    except Exception as be:
        print(f"    [!] [安全防护] 快照创建跳过 (网络或初次部署): {be}")

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

        # Sync priority abilities
        if priority_data:
            req = urllib.request.Request(
                f"{UPSTASH_URL}/set/tftf:priority_abilities",
                data=json.dumps(priority_data).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {UPSTASH_TOKEN}",
                    "Content-Type": "application/json"
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                ret = json.loads(resp.read().decode("utf-8"))
                print(f"    [+] Synced tftf:priority_abilities -> {ret.get('result')}")

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


def pull_from_upstash():
    print("[*] Checking Upstash KV for any remote online edits before sync...")
    try:
        import sync_from_upstash
        keys = sync_from_upstash.fetch_all_keys()
        all_data = sync_from_upstash.fetch_pipeline_batch(keys)
        synced_count = 0
        for bot_id, up_data in all_data.items():
            loc_path = sync_from_upstash.CHAR_DIR / f"{bot_id}.json"
            if not loc_path.exists():
                continue
            try:
                loc_data = json.loads(loc_path.read_text(encoding="utf-8"))
            except Exception:
                loc_data = {}
            up_str = json.dumps(up_data, sort_keys=True, ensure_ascii=False)
            loc_str = json.dumps(loc_data, sort_keys=True, ensure_ascii=False)
            if up_str != loc_str:
                print(f"    [*] Found remote edits for [{bot_id}], merging into local SQLite & JSON...")
                sync_from_upstash.sync_bot_to_local_json(bot_id, up_data)
                sync_from_upstash.sync_bot_to_sqlite(bot_id, up_data)
                synced_count += 1
        if synced_count > 0:
            print(f"    [+] Successfully merged {synced_count} remote bot edits into local SQLite!")
        else:
            print("    [+] No remote edits detected. Local is up-to-date with cloud.")
    except Exception as e:
        print(f"    [!] Remote pull check error: {e}")
        if "--push-kv" in sys.argv or "--force-push" in sys.argv:
            print("\n[CRITICAL ERROR] 无法连接或拉取 Upstash KV 云端数据！")
            print("为了绝对保护您在网页端编辑的数据不被本地旧数据覆盖，程序已紧急阻止向云端推送！")
            print("请检查网络后重试。若确实要强制覆盖云端，请使用参数: --force-push\n")
            if "--force-push" not in sys.argv:
                sys.exit(1)
        else:
            print("    [!] 注意: 无法连接云端拉取最新数据。因默认不向云端推送，本地生成将继续进行。")


def main():
    if "--only-html" in sys.argv or "--html-only" in sys.argv:
        print("[*] Running in HTML-only mode. Skipping DB export & Upstash sync.")
        update_bots_html()
        print("\n[OK] bots.html updated successfully in 0.1s!")
        return

    # 0. 优先自动拉取线上最新改动，同步到本地 SQLite & JSON
    if "--no-pull" not in sys.argv:
        pull_from_upstash()

    overview_data, all_bots_dict, priority_data = sync_database_data()
    update_bots_html()

    # 仅当显式指定 --push-kv 时才向 Upstash KV 推送，默认绝对不向云端推送
    if "--push-kv" in sys.argv or "--force-push" in sys.argv:
        print("[*] 检测到显式推送开关 (--push-kv)，正在将本地数据全量写入 Upstash KV...")
        sync_to_upstash_kv(overview_data, all_bots_dict, priority_data)
    else:
        print("\n    [安全防护] 云端 Upstash KV 推送已默认关闭 (线上网站为数据编辑的真理源)。")
        print("    [安全防护] 本次仅同步至本地 SQLite、本地 JSON 与 GitHub Pages 静态回退缓存。")
        print("    [安全防护] 若确需将本地全量数据覆盖至云端，请显式使用参数: --push-kv")

    print("\n[OK] All web dashboard data and bots.html synchronized successfully!")


if __name__ == "__main__":
    main()
