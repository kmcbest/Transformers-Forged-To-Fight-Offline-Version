import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path("Server").resolve()))
import gamedata

qmap = gamedata.build_raid_map()
summary = gamedata.build_raid_summary()

grid = qmap["grid"]
dim = qmap["gridDimension"]

# 1. Simulate PathAnalyzer.GetPathsFromMap()
paths = qmap["pathData"]

# 2. Simulate PathAnalyzer.GetPathsForEachTile()
tile_paths_dic = {}
for i in range(dim):
    for j in range(dim):
        tile = grid[i][j]
        pos = (i, j)
        if tile.get("walkable", False):
            # Find paths containing pos
            matched = []
            for p in paths:
                p_nodes = [(pt["x"], pt["y"]) for pt in p["path"]]
                if pos in p_nodes:
                    matched.append(p)
            tile_paths_dic[pos] = matched

print(f"Total walkable registered in tile_paths_dic: {len(tile_paths_dic)}")

# 3. Simulate PathAnalyzer.GetLinkInfo() for each non-hidden walkable tile
errors = []
for i in range(dim):
    for j in range(dim):
        tile = grid[i][j]
        if tile.get("hidden", True) or not tile.get("walkable", False):
            continue
        
        pos = (i, j)
        # Check sourceTile in tile_paths_dic
        if pos not in tile_paths_dic:
            errors.append(f"sourceTile {pos} not in tile_paths_dic!")
        
        # Check links
        links = tile.get("links", [])
        vis_links = tile.get("visibleLinks", [])
        
        # Check that vis_links corresponds to links prefix
        for k, vlink in enumerate(vis_links):
            if k >= len(links):
                errors.append(f"Tile {pos}: visibleLinks index {k} exceeds links length {len(links)}!")
            else:
                lk = links[k]
                if (vlink["x"], vlink["y"]) != (lk["x"], lk["y"]):
                    errors.append(f"Tile {pos}: visibleLinks[{k}] ({vlink}) != links[{k}] ({lk})!")
        
        for lk in links:
            dest = (lk["x"], lk["y"])
            if dest not in tile_paths_dic:
                errors.append(f"Tile {pos} has link {dest} which is MISSING from tile_paths_dic (CRASH KEYNOTFOUND)!")

if errors:
    print("ERRORS FOUND:")
    for e in errors:
        print("  -", e)
else:
    print("ALL CHECKS PASSED! No KeyNotFoundException, no index mismatch!")
