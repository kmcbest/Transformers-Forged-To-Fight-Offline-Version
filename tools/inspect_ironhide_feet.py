# -*- coding: utf-8 -*-
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Inspect Ironhide feet vertices from ironhide.obj
min_x, max_x = 0, 0
feet_verts_l = []
feet_verts_r = []

with open("tools/demolishor/ironhide_extracted/ironhide.obj", "r", encoding="utf-8", errors="ignore") as f:
    for line in f:
        if line.startswith("v "):
            parts = line.strip().split()
            x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
            # In Ironhide OBJ, height is Y. Feet are Y < 1.5
            if y < 1.5:
                if x < 0:
                    feet_verts_l.append((x, y, z))
                else:
                    feet_verts_r.append((x, y, z))

if feet_verts_l:
    xs_l = [v[0] for v in feet_verts_l]
    zs_l = [v[2] for v in feet_verts_l]
    print(f"Ironhide Left Foot: X range=[{min(xs_l):.2f}, {max(xs_l):.2f}], Z range=[{min(zs_l):.2f}, {max(zs_l):.2f}], Center X={sum(xs_l)/len(xs_l):.2f}")
if feet_verts_r:
    xs_r = [v[0] for v in feet_verts_r]
    zs_r = [v[2] for v in feet_verts_r]
    print(f"Ironhide Right Foot: X range=[{min(xs_r):.2f}, {max(xs_r):.2f}], Z range=[{min(zs_r):.2f}, {max(zs_r):.2f}], Center X={sum(xs_r)/len(xs_r):.2f}")
