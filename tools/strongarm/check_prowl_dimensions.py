import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

p_prowl = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\prowl_gs_deluxe2016_odr\prowl_gs_deluxe2016.assetbundle")
env = UnityPy.load(str(p_prowl))

for obj in env.objects:
    if obj.type.name == "Mesh":
        tree = obj.read_typetree()
        if tree.get("m_Name") == "cha_prowl_gs_deluxe2016_00":
            aabb = tree.get("m_LocalAABB")
            c = aabb["m_Center"]
            e = aabb["m_Extent"]
            print(f"Prowl Robot Mesh AABB:")
            print(f"  Center: ({c['x']:.3f}, {c['y']:.3f}, {c['z']:.3f})")
            print(f"  Extent: ({e['x']:.3f}, {e['y']:.3f}, {e['z']:.3f})")
            print(f"  Height: {e['y']*2:.3f}m, Min Y: {c['y']-e['y']:.3f}m, Max Y: {c['y']+e['y']:.3f}m")
            print(f"  Width:  {e['x']*2:.3f}m")
            print(f"  Depth:  {e['z']*2:.3f}m")

# Check Hips, Head, LeftFoot, RightFoot positions
# We already exported prowl_robot_rig.json!
import json
with open(r"E:\Agent\TFTF-blender\tools\strongarm\prowl_robot_rig.json", "r") as f:
    rig = json.load(f)

print("\nKey Prowl Rest Bone BindPoses (inverse world matrix row 3):")
for b in rig:
    name = b["name"]
    if name in ["Hips", "Spine", "Head", "LeftShoulder", "LeftArm", "LeftForeArm", "LeftHand", "LeftUpLeg", "LeftLeg", "LeftToeBase"]:
        bp = b["bindpose"]
        # bp is 4x4 matrix (m00..m33). Invert it to get bone world pos
        import numpy as np
        mat = np.array([
            [bp['e00'], bp['e01'], bp['e02'], bp['e03']],
            [bp['e10'], bp['e11'], bp['e12'], bp['e13']],
            [bp['e20'], bp['e21'], bp['e22'], bp['e23']],
            [bp['e30'], bp['e31'], bp['e32'], bp['e33']]
        ])
        inv = np.linalg.inv(mat)
        pos = inv[:3, 3]
        print(f"  {name:14s}: world pos = ({pos[0]:.3f}, {pos[1]:.3f}, {pos[2]:.3f})")
