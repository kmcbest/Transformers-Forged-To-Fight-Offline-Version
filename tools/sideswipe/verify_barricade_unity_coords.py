import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import json

p_rob = r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\00_donor_reference\cha_barricade_cin_dotm_00_robot.obj"
verts = []
with open(p_rob, "r", encoding="utf-8") as f:
    for line in f:
        if line.startswith("v "):
            parts = line.strip().split()
            verts.append((float(parts[1]), float(parts[2]), float(parts[3])))

print(f"Total Barricade vertices: {len(verts)}")
# Find vertices around head height (Y between 9.5 and 10.5)
head_vs = [v for v in verts if 9.5 < v[1] < 10.5]
hz = [v[2] for v in head_vs]
print(f"Head (Y=9.5-10.5): Z range = [{min(hz):.3f}, {max(hz):.3f}], mean Z = {sum(hz)/len(hz):.3f}")

# Find vertices around chest height (Y between 7.0 and 8.5)
chest_vs = [v for v in verts if 7.0 < v[1] < 8.5]
cz = [v[2] for v in chest_vs]
print(f"Chest (Y=7.0-8.5): Z range = [{min(cz):.3f}, {max(cz):.3f}], mean Z = {sum(cz)/len(cz):.3f}")

# Find vertices around feet (Y < 1.0)
feet_vs = [v for v in verts if v[1] < 1.0]
fz = [v[2] for v in feet_vs]
print(f"Feet (Y < 1.0): Z range = [{min(fz):.3f}, {max(fz):.3f}], mean Z = {sum(fz)/len(fz):.3f}")
