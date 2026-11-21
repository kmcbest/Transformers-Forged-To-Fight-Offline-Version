import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

p_car = r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\00_donor_reference\cha_barricade_cin_dotm_01_car.obj"
verts = []
with open(p_car, "r", encoding="utf-8") as f:
    for line in f:
        if line.startswith("v "):
            parts = line.strip().split()
            verts.append((float(parts[1]), float(parts[2]), float(parts[3])))

print(f"Total Barricade Car vertices: {len(verts)}")
zs = [v[2] for v in verts]
print(f"Barricade car Z range: [{min(zs):.3f}, {max(zs):.3f}]")

# Let's find vertices with highest/lowest Z and check if front or rear
min_z_vs = [v for v in verts if v[2] < min(zs) + 1.0]
max_z_vs = [v for v in verts if v[2] > max(zs) - 1.0]
print(f"At min Z ({min(zs):.2f}): count={len(min_z_vs)}")
print(f"At max Z ({max(zs):.2f}): count={len(max_z_vs)}")
