import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path

OBJ_PATH = Path(r"E:\Agent\TFTF-blender\3rd-party-models\BlastOff\00_donor_reference\cha_megatronus_gs_kabam_01_jet.obj")

verts = []
with open(OBJ_PATH, 'r', encoding='utf-8') as f:
    for line in f:
        if line.startswith('v '):
            p = line.strip().split()
            verts.append((float(p[1]), float(p[2]), float(p[3])))

max_z = max(verts, key=lambda v: v[2])
min_z = min(verts, key=lambda v: v[2])

print(f"Megatronus Jet OBJ: max Z vertex = {max_z}")
print(f"Megatronus Jet OBJ: min Z vertex = {min_z}")

# Check X span near max Z vs min Z
near_max_z = [v for v in verts if v[2] > 4.0]
near_min_z = [v for v in verts if v[2] < -2.0]

print(f"X span near max Z (+Z): {max(v[0] for v in near_max_z) - min(v[0] for v in near_max_z):.3f}")
print(f"X span near min Z (-Z): {max(v[0] for v in near_min_z) - min(v[0] for v in near_min_z):.3f}")
