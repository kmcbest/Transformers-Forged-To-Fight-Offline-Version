import json

with open(r"E:\Agent\TFTF-blender\tools\demolishor\ironhide_47_vh_bones.json", "r", encoding="utf-8") as f:
    vh_data = json.load(f)

print(f"Vehicle bones count: {len(vh_data['bone_order'])}")
for bname in vh_data["bone_order"]:
    mat = vh_data["bones"][bname]["matrix"]
    tx, ty, tz = mat[0][3], mat[1][3], mat[2][3]
    if any(k in bname.lower() for k in ["wheel", "base", "body", "front", "rear"]):
        print(f"Bone {bname:25s}: pos = ({tx:.3f}, {ty:.3f}, {tz:.3f})")
