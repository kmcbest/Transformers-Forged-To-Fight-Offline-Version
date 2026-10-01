with open("tools/latest_device.log", "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")
demolishor_lines = [line.strip() for line in lines if "demolishor" in line.lower()]
print(f"Lines containing 'demolishor': {len(demolishor_lines)}")
for l in demolishor_lines[:30]:
    print(l)

print("\n--- Searching for ASF, HeroesScreen, or tile creation ---")
tile_lines = [line.strip() for line in lines if any(k in line for k in ["HeroesScreen", "ASF", "ApplySorting", "Tile", "GETENT"])]
for l in tile_lines[:40]:
    print(l)
