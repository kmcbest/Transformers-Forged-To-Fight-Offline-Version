import sys
sys.path.insert(0, "Server")
import gamedata

relics = gamedata._load_relics()
relic_map = {r["id"]: r for r in relics}

for rid in ["relic_statue_op", "relic_matrix_of_leadership"]:
    if rid in relic_map:
        print(f"OK relic: {rid} -> {relic_map[rid].get('model_id')}")
    else:
        print(f"MISSING relic: {rid}")
        # search
        for r in relics:
            if "statue" in r["id"] or "matrix" in r["id"]:
                print("  found:", r["id"])
