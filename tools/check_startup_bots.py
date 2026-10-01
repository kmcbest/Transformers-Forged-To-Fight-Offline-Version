with open("tools/latest_startup.log", "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

ratewgt_bots = set()
getbp_bots = set()
http_lines = []

for l in lines:
    if "HTTP:" in l:
        http_lines.append(l.strip())
    if "RATEWGT" in l:
        parts = l.strip().split()
        if len(parts) > 1:
            ratewgt_bots.add(parts[1])
    if "GETBP" in l:
        parts = l.strip().split()
        if len(parts) > 1:
            getbp_bots.add(parts[1])

print(f"HTTP requests ({len(http_lines)}):")
for h in http_lines[:20]:
    print(" ", h)

print(f"RATEWGT bots ({len(ratewgt_bots)}): {sorted(list(ratewgt_bots))}")
print(f"GETBP bots ({len(getbp_bots)}): {sorted(list(getbp_bots))}")
