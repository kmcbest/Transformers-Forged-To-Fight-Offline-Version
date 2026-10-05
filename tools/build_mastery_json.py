import json
import os
from pathlib import Path

def generate_mastery_json():
    src_path = r"c:\Users\Xiangli496\Downloads\GET__skilltrees_skilltrees-list (defensive).json"
    with open(src_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    result = data["result"]

    # 1. Update node_off_low_rush icon to E41B and convert all icons to Unicode PUA
    nodes = result.get("nodes", [])
    for n in nodes:
        nid = n.get("id")
        icon = n.get("icon", "")
        if nid == "node_off_low_rush":
            icon = "E41B"
        
        # Convert hex string (e.g. "E41B") to unicode character
        if len(icon) == 4 and all(c in "0123456789abcdefABCDEF" for c in icon):
            icon = chr(int(icon, 16))
        n["icon"] = icon

    # 2. Reverse grid columns for st_offense and st_defense so they match editor visually
    trees = result.get("trees", [])
    offense_node_ids = set()
    defense_node_ids = set()

    for t in trees:
        tid = t.get("id")
        grid = t.get("layoutData", {}).get("grid", [])
        for col in grid:
            col.reverse()
            for cell in col:
                node_id = cell.get("node")
                if node_id:
                    if tid == "st_offense":
                        offense_node_ids.add(node_id)
                    elif tid == "st_defense":
                        defense_node_ids.add(node_id)

    # 3. Populate progression: unlock all levels & activate in treeStates
    unlocked = {}
    offense_active = {}
    defense_active = {}
    offense_sp = 0
    defense_sp = 0

    for n in nodes:
        nid = n.get("id")
        levels = n.get("levels", [])
        unlocked[nid] = {"levels": {}}
        active_dict = {}
        for lvl_info in levels:
            lvl_str = str(lvl_info["level"])
            unlocked[nid]["levels"][lvl_str] = True
            active_dict[lvl_str] = {"a": True}
        
        if nid in offense_node_ids:
            offense_active[nid] = active_dict
            offense_sp += len(levels)
        elif nid in defense_node_ids:
            defense_active[nid] = active_dict
            defense_sp += len(levels)

    result["progression"] = {
        "treeStates": {
            "st_offense": {
                "investment": {"res": {"sp": offense_sp}},
                "nodes": offense_active
            },
            "st_defense": {
                "investment": {"res": {"sp": defense_sp}},
                "nodes": defense_active
            },
            "st_utility": {
                "investment": {"res": {"sp": 0}},
                "nodes": {}
            }
        },
        "unlocked": unlocked
    }

    dst_path = "Server/responses/GET__skilltrees_skilltrees-list.json"
    with open(dst_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Generated {dst_path} successfully!")
    print(f"Total nodes: {len(nodes)}")
    print(f"Offense nodes: {len(offense_node_ids)}, SP: {offense_sp}")
    print(f"Defense nodes: {len(defense_node_ids)}, SP: {defense_sp}")
    print(f"Total unlocked nodes in progression: {len(unlocked)}")

if __name__ == "__main__":
    generate_mastery_json()
