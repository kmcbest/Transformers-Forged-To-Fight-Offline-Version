import sqlite3
import json
import re

DB_PATH = "Server/tftf_database.db"
FANDOM_JSON = "tools/fandom_bot_stats.json"

BASE_660_HP = 32402
BASE_660_ATK = 2306
BASE_660_RATING = 10140

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # 1. 确保 characters 表包含 hp, attack, rating 字段
    existing_cols = [row[1] for row in c.execute("PRAGMA table_info(characters)").fetchall()]
    if "hp" not in existing_cols:
        c.execute("ALTER TABLE characters ADD COLUMN hp INTEGER;")
        print("[+] Added column 'hp' to characters table.")
    if "attack" not in existing_cols:
        c.execute("ALTER TABLE characters ADD COLUMN attack INTEGER;")
        print("[+] Added column 'attack' to characters table.")
    if "rating" not in existing_cols:
        c.execute("ALTER TABLE characters ADD COLUMN rating INTEGER;")
        print("[+] Added column 'rating' to characters table.")
    conn.commit()

    # 2. 读取 fandom_bot_stats.json
    with open(FANDOM_JSON, "r", encoding="utf-8") as f:
        fandom = json.load(f)

    def norm(s):
        return re.sub(r"[^a-z0-9]", "", s.lower())

    # 3. 遍历数据库中所有角色
    db_chars = c.execute("SELECT bot_id, name_en, name_zh, class, health_mult, attack_mult FROM characters").fetchall()
    
    updated_count = 0
    fandom_exact_count = 0
    calculated_count = 0

    for bot in db_chars:
        bid = bot["bot_id"]
        name_en = bot["name_en"]
        h_mult = bot["health_mult"] or 1.0
        a_mult = bot["attack_mult"] or 1.0
        
        # 寻找匹配的 fandom 数据
        matched_stat = None
        norm_name = norm(name_en)
        norm_bid = norm(bid)

        # 优先全字匹配
        for k, v in fandom.items():
            if norm(k) == norm_name:
                matched_stat = v
                break

        # 其次 bot_id 包含
        if not matched_stat:
            for k, v in fandom.items():
                nk = norm(k)
                if nk in norm_bid or norm_bid.startswith(nk):
                    matched_stat = v
                    break

        final_hp = None
        final_atk = None
        final_rat = None
        source_tag = ""

        # 如果 fandom 数据有效且是 6/60 级别（HP > 10000）
        if matched_stat and matched_stat.get("health") and matched_stat["health"] >= 10000:
            final_hp = matched_stat["health"]
            final_atk = matched_stat["attack"]
            final_rat = matched_stat["rating"]
            source_tag = f"Fandom ({matched_stat.get('match_type', 'exact')})"
            fandom_exact_count += 1
        else:
            # 采用 6/60 标准基准乘倍率计算
            final_hp = round(BASE_660_HP * h_mult)
            final_atk = round(BASE_660_ATK * a_mult)
            final_rat = round(final_hp * 0.125 + final_atk * 1.5 + 2500)
            source_tag = f"Calculated ({h_mult:.2f}x / {a_mult:.2f}x)"
            calculated_count += 1

        c.execute("""
            UPDATE characters 
            SET hp = ?, attack = ?, rating = ?, updated_at = CURRENT_TIMESTAMP
            WHERE bot_id = ?
        """, (final_hp, final_atk, final_rat, bid))
        updated_count += 1
        print(f"[{updated_count}/{len(db_chars)}] {name_en:<22} ({bid:<26}) -> HP: {final_hp:<6} | ATK: {final_atk:<5} | Rating: {final_rat:<6} [{source_tag}]")

    conn.commit()
    conn.close()

    print(f"\n=======================================================")
    print(f"[OK] 成功更新数据库中的 {updated_count} 个角色！")
    print(f"     - Fandom 数据直接写入: {fandom_exact_count} 个")
    print(f"     - 基准公式补全: {calculated_count} 个")
    print(f"=======================================================\n")

if __name__ == "__main__":
    main()
