import sys
sys.path.insert(0, "Server")
import gamedata

mods = gamedata._load_mods()
for m in sorted(mods, key=lambda x: x["id"]):
    print(f"{m['id']:30s} -> model={m.get('model_id')}")
