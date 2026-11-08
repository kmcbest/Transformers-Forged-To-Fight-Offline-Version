import json

with open(r"E:\Agent\TFTF-blender\tools\vortex\grindor_78_authoritative_bindposes.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Unity (ux, uy, uz) -> Blender (ux, uz, uy)
for bname, info in sorted(data.items(), key=lambda x: x[1]["index"]):
    p = info["world_pos"]
    bx, by, bz = p["x"], p["z"], p["y"]
    if any(k in bname.lower() for k in ["hips", "spine", "head", "arm", "hand", "leg", "foot"]):
        print(f"[{info['index']:2d}] {bname:20s} Unity: ({p['x']:6.2f}, {p['y']:6.2f}, {p['z']:6.2f}) -> Blender: ({bx:6.2f}, {by:6.2f}, {bz:6.2f})")
