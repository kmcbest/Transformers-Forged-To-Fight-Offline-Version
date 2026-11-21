import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json

verts = []
with open("3rd-party-models/swoop/01_master/ramjet_official_01.obj", "r", encoding="utf-8") as f:
    for line in f:
        if line.startswith("v "):
            parts = line.strip().split()[1:]
            verts.append([float(p) for p in parts])

xs = [v[0] for v in verts]
ys = [v[1] for v in verts]
zs = [v[2] for v in verts]
print(f"Ramjet Jet 01 OBJ bounds:")
print(f"  X: [{min(xs):.3f}, {max(xs):.3f}] (span: {max(xs)-min(xs):.3f}m - Wingspan)")
print(f"  Y: [{min(ys):.3f}, {max(ys):.3f}] (span: {max(ys)-min(ys):.3f}m - Height in Unity)")
print(f"  Z: [{min(zs):.3f}, {max(zs):.3f}] (span: {max(zs)-min(zs):.3f}m - Length in Unity)")

with open("tools/swoop/ramjet_jet_29_authoritative_bindposes.json", "r", encoding="utf-8") as f:
    jet_data = json.load(f)

print(f"Ramjet Jet bone count: {jet_data['bone_count']}")
for bname in ["Reference", "COG", "chop1_chest_center", "L_wing", "R_wing", "nose_cone"]:
    if bname in jet_data["bones"]:
        print(f"  Jet bone {bname:20s}: {jet_data['bones'][bname]['unity_world_pos']}")
