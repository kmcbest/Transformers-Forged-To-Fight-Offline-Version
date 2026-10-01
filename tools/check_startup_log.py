with open("tools/latest_startup.log", "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")
for l in lines:
    if "payload" in l.lower() or "map_payload" in l:
        print(l.rstrip())
    if "demolishor" in l.lower():
        print(l.rstrip())
