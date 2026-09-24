# -*- coding: utf-8 -*-
import sys

sys.stdout.reconfigure(encoding='utf-8')

all_verts = []
with open("tools/demolishor/ironhide_extracted/ironhide.obj", "r", encoding="utf-8", errors="ignore") as f:
    for line in f:
        if line.startswith("v "):
            parts = line.strip().split()
            x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
            all_verts.append((x, y, z))

print(f"Total verts: {len(all_verts)}")
# Ironhide OBJ: Y is Up, X is Right, Z is Forward
print(f"X (width): [{min(v[0] for v in all_verts):.2f}, {max(v[0] for v in all_verts):.2f}]")
print(f"Y (height): [{min(v[1] for v in all_verts):.2f}, {max(v[1] for v in all_verts):.2f}]")
print(f"Z (depth): [{min(v[2] for v in all_verts):.2f}, {max(v[2] for v in all_verts):.2f}]")

# Check arms/cannons: Y in [4.0, 7.5], |X| > 2.0
arm_l = [v for v in all_verts if v[1] >= 4.0 and v[1] <= 7.5 and v[0] < -2.0]
arm_r = [v for v in all_verts if v[1] >= 4.0 and v[1] <= 7.5 and v[0] > 2.0]
print(f"Left Arm/Cannon: count={len(arm_l)}, X=[{min(v[0] for v in arm_l):.2f}, {max(v[0] for v in arm_l):.2f}], Z=[{min(v[2] for v in arm_l):.2f}, {max(v[2] for v in arm_l):.2f}]")
print(f"Right Arm/Cannon: count={len(arm_r)}, X=[{min(v[0] for v in arm_r):.2f}, {max(v[0] for v in arm_r):.2f}], Z=[{min(v[2] for v in arm_r):.2f}, {max(v[2] for v in arm_r):.2f}]")
