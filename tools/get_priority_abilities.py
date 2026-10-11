#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TFTF Priority Abilities Query & Export Tool
===========================================
从“TFTF 角色数值与技能中枢 (Transformers Forged to Fight)”真理源查询优先待办能力 (status='priority')，
并稳定生成格式规整、UTF-8 编码的 priority_ab_clean.txt 与 priority_abilities_clean.txt。

真理源层级 (Source of Truth Hierarchy):
  1. 动态云数据库 Upstash KV: tftf:priority_abilities (实时在线最新)
  2. 本地项目数据源: D:/docforall/GitHub/kmcbest.github.io/tftfr/data/priority_abilities.json
  3. 静态真理源 CDN: https://kmcbest.github.io/tftfr/data/priority_abilities.json
  4. 本地 SQLite 缓存: Server/tftf_database.db

支持功能:
  - 自动输出到 tools/priority_ab_clean.txt 与 tools/priority_abilities_clean.txt
  - 自动检测代码落地状态 (Server 脚本与 Native C 技能模块)
  - 支持按角色名/bot_id 过滤 (--bot <keyword>)
  - 支持全量扫描云端所有角色重新汇总待办 (--scan-all / --rebuild)
  - 支持将云端待办同步回本地 SQLite 数据库 (--sync-db)
"""

import os
import sys
import json
import time
import argparse
import urllib.request
from pathlib import Path
from datetime import datetime

# Windows 控制台编码保护
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

REPO_ROOT = Path(__file__).resolve().parent.parent
LOCAL_TFTFR_DATA = Path("d:/docforall/GitHub/kmcbest.github.io/tftfr/data/priority_abilities.json")
DB_PATH = REPO_ROOT / "Server" / "tftf_database.db"

UPSTASH_URL = "https://deciding-bulldog-136761.upstash.io"
UPSTASH_READ_TOKEN = "ggAAAAAAAhY5AAIgcDG7a511dMnvUap5JjML7kdCMH0hQAG95-3BtwD6YEaFeQ"
UPSTASH_WRITE_TOKEN = "gQAAAAAAAhY5AAIgcDEyZGMwZDRhNzRlZGQ0MDI2YWM2YmI3ZDExNTc3ZjZmNA"
CDN_URL = "https://kmcbest.github.io/tftfr/data/priority_abilities.json"

CATEGORY_NAMES = {
    "basic": "基础能力 (Basic)",
    "passive": "被动能力 (Passive)",
    "signature": "觉醒能力 (Signature)",
    "sp1": "特殊技 1 (SP1)",
    "sp2": "特殊技 2 (SP2)",
    "sp3": "特殊技 3 (SP3)",
    "synergy": "协同能力 (Synergy)",
}

CLASS_NAMES = {
    "braw": "格斗系 (Brawler)",
    "brawler": "格斗系 (Brawler)",
    "scou": "侦察系 (Scout)",
    "scout": "侦察系 (Scout)",
    "warr": "战士系 (Warrior)",
    "warrior": "战士系 (Warrior)",
    "tact": "战术系 (Tactician)",
    "tactician": "战术系 (Tactician)",
    "tech": "科技系 (Tech)",
    "demo": "爆破系 (Demolition)",
    "demolition": "爆破系 (Demolition)",
}


def fetch_from_upstash_priority():
    """从 Upstash KV 直接读取 tftf:priority_abilities"""
    url = f"{UPSTASH_URL}/get/tftf:priority_abilities"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {UPSTASH_READ_TOKEN}"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            raw = data.get("result")
            if not raw:
                return None
            payload = json.loads(raw) if isinstance(raw, str) else raw
            return payload.get("abilities", [])
    except Exception as e:
        print(f"[!] Upstash priority_abilities read failed: {e}", file=sys.stderr)
        return None


def fetch_from_upstash_scan_all():
    """扫描 Upstash KV 中的全部 tftf:char:*，汇总结聚全部 status == 'priority' 的能力"""
    print("[*] Performing deep scan across all characters in Upstash KV...", file=sys.stderr)
    req_keys = urllib.request.Request(f"{UPSTASH_URL}/keys/tftf:char:*", headers={"Authorization": f"Bearer {UPSTASH_READ_TOKEN}"})
    try:
        with urllib.request.urlopen(req_keys, timeout=15) as resp:
            keys = json.loads(resp.read().decode("utf-8")).get("result", [])
    except Exception as e:
        print(f"[!] Upstash keys list failed: {e}", file=sys.stderr)
        return None

    if not keys:
        return None

    # Overview for names
    bot_map = {}
    try:
        req_ov = urllib.request.Request(f"{UPSTASH_URL}/get/tftf:overview", headers={"Authorization": f"Bearer {UPSTASH_READ_TOKEN}"})
        with urllib.request.urlopen(req_ov, timeout=10) as resp:
            raw_ov = json.loads(resp.read().decode("utf-8")).get("result")
            ov = json.loads(raw_ov) if isinstance(raw_ov, str) else (raw_ov or {})
            for c in ov.get("characters", []):
                bot_map[c["bot_id"]] = c
    except Exception:
        pass

    chunk_size = 20
    all_priority = []
    for i in range(0, len(keys), chunk_size):
        chunk = keys[i:i + chunk_size]
        cmds = [["GET", k] for k in chunk]
        req_pipe = urllib.request.Request(
            f"{UPSTASH_URL}/pipeline",
            headers={"Authorization": f"Bearer {UPSTASH_READ_TOKEN}", "Content-Type": "application/json"},
            data=json.dumps(cmds).encode("utf-8")
        )
        try:
            with urllib.request.urlopen(req_pipe, timeout=20) as resp:
                res_list = json.loads(resp.read().decode("utf-8"))
                for k, item in zip(chunk, res_list):
                    val = item.get("result")
                    if not val:
                        continue
                    char_data = json.loads(val) if isinstance(val, str) else val
                    bid = k.replace("tftf:char:", "")
                    binfo = bot_map.get(bid, {})
                    bname_zh = binfo.get("name_zh") or char_data.get("name_zh") or bid
                    bname_en = binfo.get("name_en") or char_data.get("name_en") or bid
                    bclass = binfo.get("class") or char_data.get("class") or ""
                    bfaction = binfo.get("faction") or char_data.get("faction") or ""

                    for ab in char_data.get("abilities", []):
                        st = (ab.get("status") or "").strip().lower()
                        if st == "priority":
                            all_priority.append({
                                "id": ab.get("id"),
                                "bot_id": bid,
                                "bot_name_zh": bname_zh,
                                "bot_name_en": bname_en,
                                "bot_class": bclass,
                                "bot_faction": bfaction,
                                "bot_source": "Kabam",
                                "category": ab.get("category"),
                                "title_zh": ab.get("title_zh"),
                                "title_en": ab.get("title_en"),
                                "desc_zh": ab.get("desc_zh"),
                                "desc_en": ab.get("desc_en"),
                                "pua_icon": ab.get("pua_icon"),
                                "synergy_bots": ab.get("synergy_bots") or [],
                                "status": "priority",
                                "sort_order": ab.get("sort_order", 0)
                            })
        except Exception as e:
            print(f"[!] Pipeline batch error for chunk {i}: {e}", file=sys.stderr)

    # 尝试把最新结果写回 Upstash KV 的 tftf:priority_abilities
    if all_priority:
        try:
            payload = {
                "total": len(all_priority),
                "status": "priority",
                "abilities": all_priority
            }
            req_set = urllib.request.Request(
                f"{UPSTASH_URL}/set/tftf:priority_abilities",
                headers={"Authorization": f"Bearer {UPSTASH_WRITE_TOKEN}", "Content-Type": "application/json"},
                data=json.dumps(payload).encode("utf-8")
            )
            with urllib.request.urlopen(req_set, timeout=10) as resp:
                pass
            print(f"[*] Successfully rebuilt online tftf:priority_abilities ({len(all_priority)} items)", file=sys.stderr)
        except Exception as e:
            print(f"[!] Failed to write back rebuilt priority list: {e}", file=sys.stderr)

    return all_priority


def fetch_from_local_file():
    """从本地 tftfr 静态数据源读取"""
    if LOCAL_TFTFR_DATA.exists():
        try:
            with open(LOCAL_TFTFR_DATA, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("abilities", [])
        except Exception as e:
            print(f"[!] Local file read failed: {e}", file=sys.stderr)
    return None


def fetch_from_cdn():
    """从 GitHub Pages 静态 CDN 读取"""
    req = urllib.request.Request(CDN_URL, headers={"User-Agent": "TFTF-Agent/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("abilities", [])
    except Exception as e:
        print(f"[!] CDN fetch failed: {e}", file=sys.stderr)
        return None


def fetch_from_sqlite():
    """从本地 Server/tftf_database.db 读取"""
    if not DB_PATH.exists():
        return None
    try:
        import sqlite3
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        rows = c.execute("""
            SELECT ca.id, ca.bot_id, c.name_zh AS bot_name_zh, c.name_en AS bot_name_en,
                   c.class AS bot_class, c.faction AS bot_faction, c.source AS bot_source,
                   ca.category, ca.title_zh, ca.title_en, ca.desc_zh, ca.desc_en,
                   ca.pua_icon, ca.synergy_bots, ca.status, ca.sort_order
            FROM character_abilities ca
            LEFT JOIN characters c ON ca.bot_id = c.bot_id
            WHERE ca.status = 'priority'
            ORDER BY ca.bot_id, ca.id
        """).fetchall()
        items = []
        for r in rows:
            d = dict(r)
            if d.get("synergy_bots"):
                try:
                    d["synergy_bots"] = json.loads(d["synergy_bots"])
                except Exception:
                    d["synergy_bots"] = []
            else:
                d["synergy_bots"] = []
            items.append(d)
        conn.close()
        return items
    except Exception as e:
        print(f"[!] SQLite query failed: {e}", file=sys.stderr)
        return None


def check_implementation_status(bot_id, ability_id=None):
    """检测指定机体和能力的落地实现代码状态"""
    server_dir = REPO_ROOT / "Server" / "abilities" / "bots"
    server_file = server_dir / f"{bot_id}.py"
    server_status = "未落地"
    server_path = None
    if server_file.exists():
        server_status = "已建模块"
        server_path = f"Server/abilities/bots/{bot_id}.py"
        if ability_id:
            try:
                content = server_file.read_text(encoding="utf-8")
                if str(ability_id) in content:
                    server_status = "已实现"
            except Exception:
                pass

    native_dir = REPO_ROOT / "tools" / "nativehook" / "skills" / "bots"
    native_status = "未落地"
    native_path = None
    if native_dir.exists():
        for f in native_dir.glob("*.c"):
            try:
                c_text = f.read_text(encoding="utf-8")
                if bot_id in c_text:
                    native_path = f"tools/nativehook/skills/bots/{f.name}"
                    native_status = "已建模块"
                    if ability_id and str(ability_id) in c_text:
                        native_status = "已实现"
                    break
            except Exception:
                pass

    return {
        "server": server_status,
        "server_path": server_path,
        "native": native_status,
        "native_path": native_path
    }


def format_clean_text(abilities, source_name):
    """格式化生成高可读性、无乱码的 clean txt 报告"""
    lines = []
    lines.append("=" * 88)
    lines.append("  TFTF 角色数值与技能中枢 - 优先待办能力清单 (Priority Abilities Source of Truth)")
    lines.append(f"  生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 真理源: {source_name}")
    lines.append(f"  待办总数: {len(abilities)} 条")
    lines.append("=" * 88)
    lines.append("")

    # 按角色分组
    by_bot = {}
    for ab in abilities:
        bid = ab.get("bot_id", "unknown")
        if bid not in by_bot:
            by_bot[bid] = {
                "bot_id": bid,
                "name_zh": ab.get("bot_name_zh") or bid,
                "name_en": ab.get("bot_name_en") or bid,
                "class": ab.get("bot_class") or "-",
                "faction": ab.get("bot_faction") or "-",
                "abilities": []
            }
        by_bot[bid]["abilities"].append(ab)

    for bid, binfo in by_bot.items():
        bot_impl = check_implementation_status(bid)
        class_disp = CLASS_NAMES.get(binfo["class"].lower(), binfo["class"])
        lines.append("┌" + "─" * 86 + "┐")
        lines.append(f"│ 机体: 【{binfo['name_zh']} / {binfo['name_en']}】 ({bid})")
        lines.append(f"│ 职业: {class_disp} | 阵营: {binfo['faction']} | 待办数量: {len(binfo['abilities'])} 项")
        lines.append(f"│ 代码落地基线: Server: [{bot_impl['server']}] {bot_impl['server_path'] or '无'} | Native: [{bot_impl['native']}] {bot_impl['native_path'] or '无'}")
        lines.append("└" + "─" * 86 + "┘")

        for ab in binfo["abilities"]:
            aid = ab.get("id")
            ab_impl = check_implementation_status(bid, aid)
            cat_disp = CATEGORY_NAMES.get(ab.get("category"), ab.get("category") or "OTHER")
            title_zh = ab.get("title_zh") or "未命名"
            title_en = ab.get("title_en") or ""
            title_str = f"{title_zh} / {title_en}".strip(" /")
            pua_str = f"PUA: {ab.get('pua_icon')}" if ab.get("pua_icon") else "PUA: 无"

            lines.append(f"  [ID: {aid}] [{cat_disp}] {title_str}")
            lines.append(f"    • 状态: {ab.get('status')} | {pua_str} | Server:[{ab_impl['server']}] Native:[{ab_impl['native']}]")

            desc_zh = (ab.get("desc_zh") or "").strip()
            if desc_zh:
                zh_lines = desc_zh.split("\n")
                lines.append(f"    • 效果描述: {zh_lines[0]}")
                for zhl in zh_lines[1:]:
                    lines.append(f"               {zhl}")

            desc_en = (ab.get("desc_en") or "").strip()
            if desc_en:
                en_lines = desc_en.split("\n")
                lines.append(f"    • 英文原文: {en_lines[0]}")
                for enl in en_lines[1:]:
                    lines.append(f"               {enl}")

            if ab.get("synergy_bots"):
                lines.append(f"    • 协同机体: {', '.join(ab['synergy_bots'])}")
            lines.append("    " + "·" * 80)
        lines.append("")

    lines.append("=" * 88)
    lines.append("  [提示] 智能体实现上述能力时，请在 Server/abilities/bots/ 与 tools/nativehook/skills/bots/ 中落地，")
    lines.append("         并在代码中保留对应的能力 ID 注释 (如 [ID: 2724]) 便于自动溯源对齐。")
    lines.append("=" * 88)
    return "\n".join(lines)


def sync_to_sqlite(abilities):
    """将获取到的优先技能同步更新到本地 Server/tftf_database.db 中"""
    if not DB_PATH.exists():
        return
    try:
        import sqlite3
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        for ab in abilities:
            aid = ab.get("id")
            if not aid:
                continue
            # 更新或确保 status='priority'
            c.execute("UPDATE character_abilities SET status = 'priority' WHERE id = ?", (aid,))
        conn.commit()
        conn.close()
        print(f"[*] Synced {len(abilities)} priority abilities into {DB_PATH.name}", file=sys.stderr)
    except Exception as e:
        print(f"[!] SQLite sync error: {e}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="TFTF Priority Abilities Query & Clean TXT Exporter")
    parser.add_argument("--bot", dest="bot_filter", default=None, help="Filter by bot ID or character name (e.g. optimus, 大黄蜂)")
    parser.add_argument("--out", default="tools/priority_ab_clean.txt", help="Output text file path (default: tools/priority_ab_clean.txt)")
    parser.add_argument("--scan-all", "--rebuild", action="store_true", help="Deep scan all characters from Upstash KV to rebuild priority list")
    parser.add_argument("--sync-db", action="store_true", help="Sync retrieved priority abilities into local SQLite database")
    parser.add_argument("--json", action="store_true", help="Output raw JSON to stdout")
    parser.add_argument("--quiet", action="store_true", help="Do not print text report to console, only write files")
    args = parser.parse_args()

    source_used = None
    abilities = None

    # 1. 深度扫描模式
    if args.scan_all:
        abilities = fetch_from_upstash_scan_all()
        if abilities:
            source_used = "Upstash KV (Deep Scan All tftf:char:*)"

    # 2. 默认优先从 Upstash KV 实时聚合读取
    if abilities is None:
        abilities = fetch_from_upstash_priority()
        if abilities:
            source_used = "Upstash KV (live: tftf:priority_abilities)"

    # 3. 失败时回退到本地 tftfr 数据源
    if abilities is None:
        abilities = fetch_from_local_file()
        if abilities:
            source_used = "Local Repository (tftfr/data/priority_abilities.json)"

    # 4. 回退到静态真理源 CDN
    if abilities is None:
        abilities = fetch_from_cdn()
        if abilities:
            source_used = "Static CDN (kmcbest.github.io/tftfr/data/priority_abilities.json)"

    # 5. 回退到本地 SQLite
    if abilities is None:
        abilities = fetch_from_sqlite()
        if abilities:
            source_used = "Local SQLite Database (Server/tftf_database.db)"

    if not abilities:
        print("[ERROR] Failed to fetch priority abilities from any source!", file=sys.stderr)
        sys.exit(1)

    # 过滤
    if args.bot_filter:
        kw = args.bot_filter.strip().lower()
        abilities = [
            ab for ab in abilities
            if kw in ab.get("bot_id", "").lower()
            or kw in (ab.get("bot_name_zh") or "").lower()
            or kw in (ab.get("bot_name_en") or "").lower()
        ]

    # 同步到 SQLite
    if args.sync_db:
        sync_to_sqlite(abilities)

    if args.json:
        print(json.dumps({"total": len(abilities), "source": source_used, "abilities": abilities}, ensure_ascii=False, indent=2))
        return

    # 生成 Clean TXT 报告
    clean_text = format_clean_text(abilities, source_used)

    # 输出到目标文件 (同时写入 tools/priority_ab_clean.txt 与 tools/priority_abilities_clean.txt)
    out_path_1 = REPO_ROOT / args.out
    out_path_1.parent.mkdir(parents=True, exist_ok=True)
    out_path_1.write_text(clean_text, encoding="utf-8")

    out_path_2 = REPO_ROOT / "tools" / "priority_abilities_clean.txt"
    if out_path_2 != out_path_1:
        out_path_2.write_text(clean_text, encoding="utf-8")

    if not args.quiet:
        print(clean_text)

    print(f"\n[SUCCESS] Clean priority abilities exported to:")
    print(f"  - {out_path_1.relative_to(REPO_ROOT) if out_path_1.is_relative_to(REPO_ROOT) else out_path_1}")
    if out_path_2 != out_path_1:
        print(f"  - {out_path_2.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
