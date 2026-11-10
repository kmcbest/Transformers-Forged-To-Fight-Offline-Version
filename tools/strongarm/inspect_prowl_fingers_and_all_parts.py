import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
import numpy as np
import bpy
from pathlib import Path

# 1. Inspect Prowl's official bindpose axes for LeftArm, LeftForeArm, LeftHand, LeftHandIndex1..3, LeftHandThumb1..3
with open(r"E:\Agent\TFTF-blender\tools\strongarm\prowl_robot_rig.json", "r", encoding="utf-8") as f:
    prowl_bones = {b["name"]: b for b in json.load(f)}

print("=== Prowl BindPose Local Axes in Unity World (Right-hand / Left-hand Columns) ===")
for bn in ["LeftShoulder", "LeftArm", "LeftForeArm", "LeftHand", "LeftHandIndex1", "LeftHandIndex2", "LeftHandThumb1", "LeftHandThumb2", "LeftHandMiddle1", "LeftHandPinky1"]:
    bp = prowl_bones[bn]["bindpose"]
    M = np.array([
        [bp['e00'], bp['e01'], bp['e02'], bp['e03']],
        [bp['e10'], bp['e11'], bp['e12'], bp['e13']],
        [bp['e20'], bp['e21'], bp['e22'], bp['e23']],
        [bp['e30'], bp['e31'], bp['e32'], bp['e33']],
    ])
    inv = np.linalg.inv(M)
    pos = inv[:3, 3]
    # Bone local +X, +Y, +Z directions in Unity world space:
    ax = inv[:3, 0]
    ay = inv[:3, 1]
    az = inv[:3, 2]
    print(f"  {bn:18s} pos=({pos[0]:+.3f},{pos[1]:+.3f},{pos[2]:+.3f}) localX={ax.round(2)} localY={ay.round(2)} localZ={az.round(2)}")

# 2. Quick check of which meshes & vgroups exist in Strongarm.fbx
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r"E:\Agent\RID_game\strongarm_zip_extracted\source\Strongarm.fbx")
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
arm.data.pose_position = 'REST'
bpy.context.view_layer.update()

print("\n=== ALL Strongarm.fbx Meshes where vgs don't match name or hand/arm parts ===")
for o in sorted(bpy.data.objects, key=lambda x: x.name):
    if o.type != 'MESH':
        continue
    if any(k in o.name.lower() for k in ("hand", "palm", "arm", "elbow", "shoulder", "light", "fender")):
        if "_r" in o.name.lower() and not "shoulder" in o.name.lower():
            continue
        # get world positions using modifier? Check bone rest head pos of active vgs
        active = set()
        for v in o.data.vertices:
            for g in v.groups:
                if g.weight > 0.05:
                    active.add(o.vertex_groups[g.group].name)
        print(f"  {o.name:28s}: verts={len(o.data.vertices):4d} active_vgs={sorted(active)}")
