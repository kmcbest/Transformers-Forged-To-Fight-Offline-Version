import json

with open("tools/demolishor/ironhide_80_bones.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"{'Bone Name':20s} | {'Blender X':>10s} {'Blender Y':>10s} {'Blender Z':>10s}")
print("-" * 56)
for name in data['bone_order']:
    if any(k in name for k in ['Hips', 'Spine', 'Neck', 'Head', 'Arm', 'Leg', 'Foot', 'Hand', 'Root']):
        mat = data['bones'][name]['matrix']
        ux = mat[0][3]
        uy = mat[1][3]
        uz = mat[2][3]
        # Blender: bx = ux, by = uz, bz = uy
        bx, by, bz = ux, uz, uy
        print(f"{name:20s} | {bx:10.3f} {by:10.3f} {bz:10.3f}")
