import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import numpy as np

pts = []
with open(r"e:\Agent\TFTF-blender\3rd-party-models\swoop\01_master\ramjet_official_00.obj", "r", encoding="utf-8") as f:
    for line in f:
        if line.startswith("v "):
            parts = line.strip().split()
            pts.append([float(parts[1]), float(parts[2]), float(parts[3])])

pts = np.array(pts)
print("Ramjet Official 00 OBJ Bounds (Unity coords: Y is height):")
print(f"  X: [{pts[:,0].min():.3f}, {pts[:,0].max():.3f}], span={np.ptp(pts[:,0]):.3f}")
print(f"  Y: [{pts[:,1].min():.3f}, {pts[:,1].max():.3f}], span={np.ptp(pts[:,1]):.3f} (Height)")
print(f"  Z: [{pts[:,2].min():.3f}, {pts[:,2].max():.3f}], span={np.ptp(pts[:,2]):.3f} (Depth)")

# Check head, feet, hands positions from authoritative bindposes
import json
with open(r"e:\Agent\TFTF-blender\tools\swoop\ramjet_78_authoritative_bindposes.json", "r", encoding="utf-8") as f:
    d = json.load(f)

print("\nKey Ramjet Bone World Positions (Unity):")
for b in ["Hips", "Head", "LeftFoot", "RightFoot", "LeftHand", "RightHand", "LeftShoulderPad", "RightShoulderPad"]:
    if b in d["bones"]:
        print(f"  {b:18s}: {d['bones'][b]['unity_world_pos']}")
