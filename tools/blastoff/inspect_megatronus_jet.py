import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
from pathlib import Path
import numpy as np

OBJ_PATH = Path(r"E:\Agent\TFTF-blender\3rd-party-models\BlastOff\00_donor_reference\cha_megatronus_gs_kabam_01_jet.obj")
DONOR_JSON = Path(r"E:\Agent\TFTF-blender\3rd-party-models\BlastOff\00_donor_reference\donor_summary.json")

print("=== Reading Megatronus Jet OBJ ===")
xs, ys, zs = [], [], []
with open(OBJ_PATH, 'r', encoding='utf-8') as f:
    for line in f:
        if line.startswith('v '):
            parts = line.strip().split()
            x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
            xs.append(x)
            ys.append(y)
            zs.append(z)

print(f"Vertex count: {len(xs)}")
print(f"X: min={min(xs):.3f}, max={max(xs):.3f}, size={max(xs)-min(xs):.3f}")
print(f"Y: min={min(ys):.3f}, max={max(ys):.3f}, size={max(ys)-min(ys):.3f}")
print(f"Z: min={min(zs):.3f}, max={max(zs):.3f}, size={max(zs)-min(zs):.3f}")

donor = json.loads(DONOR_JSON.read_text(encoding='utf-8'))
mesh_01 = donor['meshes']['cha_megatronus_gs_kabam_01']
avatar_01 = donor['avatars']['cha_megatronus_gs_kabam_01Avatar']['tos']

print(f"\nMegatronus 01 bone count: {mesh_01['boneCount']}")
root_h = mesh_01['rootBoneHash']
print(f"Root bone hash: {root_h} -> {avatar_01.get(str(root_h))}")

print("\nAll bones in mesh 01:")
for h in mesh_01['boneHashes']:
    name = avatar_01.get(str(h), f"hash_{h}")
    print(f"  {h} : {name}")
