import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
import json
import math
import mathutils
from pathlib import Path

with open(r"E:\Agent\TFTF-blender\tools\strongarm\prowl_robot_rig.json", "r", encoding="utf-8") as f:
    prowl_bones = json.load(f)

pb_bl = {}
for b in prowl_bones:
    bp = b["bindpose"]
    import numpy as np
    mat = np.array([
        [bp['e00'], bp['e01'], bp['e02'], bp['e03']],
        [bp['e10'], bp['e11'], bp['e12'], bp['e13']],
        [bp['e20'], bp['e21'], bp['e22'], bp['e23']],
        [bp['e30'], bp['e31'], bp['e32'], bp['e33']]
    ])
    inv = np.linalg.inv(mat)
    pb_bl[b["name"]] = mathutils.Vector((-inv[0, 3], inv[2, 3], inv[1, 3]))

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r"E:\Agent\RID_game\strongarm_zip_extracted\source\Strongarm.fbx")
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
arm.data.pose_position = 'REST'
bpy.context.view_layer.update()

# 1. Print all unique orig_arm bone names used across ALL 124 meshes
all_used_bones = {}
for o in sorted(bpy.data.objects, key=lambda x: x.name):
    if o.type != 'MESH':
        continue
    if o.name in ("bot:mask_geo", "bot:faceMaskOn_jaw_geo"):
        continue
    for v in o.data.vertices:
        for g in v.groups:
            if g.weight > 0.05:
                bn = o.vertex_groups[g.group].name
                all_used_bones.setdefault(bn, set()).add(o.name)

print(f"=== All {len(all_used_bones)} Active Maya Bones in Strongarm.fbx ===")
for bn in sorted(all_used_bones.keys()):
    meshes = sorted(all_used_bones[bn])
    sample = ", ".join(meshes[:3]) + (f" (+{len(meshes)-3})" if len(meshes) > 3 else "")
    print(f"  {bn:24s} -> {sample}")

# 2. Compute exact Blender coordinates of Left Hand & Fingers after rotating to +7.5 deg flare
# Apply armature + Maya->Blender coords (using same scale 46.4292)
b_sh = arm.data.bones["bot:jt_shoulder_L"].head_local.copy()
b_wr = arm.data.bones["bot:jt_wrist_L"].head_local.copy()
arm_vec = b_wr - b_sh
cur_angle = math.atan2(arm_vec.x, -arm_vec.y)
target_flare_deg = 7.5
rot_rad = -(cur_angle - math.radians(target_flare_deg))
print(f"\nRaw jt_shoulder_L->jt_wrist_L angle = {math.degrees(cur_angle):.2f} deg, rotating by {math.degrees(rot_rad):.2f} deg for +{target_flare_deg} deg flare")

# Build exact transform: rot_rad around Z at b_sh, then +90X, then diag(s, -s, s), +14cm shoulder alignment X
s = 46.4292
R_arm = mathutils.Matrix.Translation(b_sh) @ mathutils.Matrix.Rotation(rot_rad, 4, 'Z') @ mathutils.Matrix.Translation(-b_sh)
R_mb = mathutils.Matrix.Diagonal((s, -s, s, 1.0)) @ mathutils.Matrix.Rotation(1.5707963, 4, 'X')
# Check shoulderBall_geo_L shift too (+0.139m)
M_full = mathutils.Matrix.Translation((0.139, -0.059, 0.0)) @ R_mb @ R_arm

print("\n=== Strongarm Left Arm & Finger Joints (After +7.5 deg flare) vs Prowl Bones ===")
pairs = [
    ("bot:jt_clav_L", "LeftShoulder"),
    ("bot:jt_shoulder_L", "LeftArm"),
    ("bot:jt_elbow_L", "LeftForeArm"),
    ("bot:jt_wrist_L", "LeftHand"),
    ("bot:jt_thumb1_L", "LeftHandThumb1"),
    ("bot:jt_thumb2_L", "LeftHandThumb2"),
    ("bot:jt_thumb3_L", "LeftHandThumb3"),
    ("bot:jt_index1_L", "LeftHandIndex1"),
    ("bot:jt_index2_L", "LeftHandIndex2"),
    ("bot:jt_index3_L", "LeftHandIndex3"),
    ("bot:jt_middle1_L", "LeftHandMiddle1"),
    ("bot:jt_middle2_L", "LeftHandMiddle2"),
    ("bot:jt_middle3_L", "LeftHandMiddle3"),
    ("bot:jt_ring1_L", "LeftHandRing1"),
    ("bot:jt_ring2_L", "LeftHandRing2"),
    ("bot:jt_ring3_L", "LeftHandRing3"),
    ("bot:jt_pinky1_L", "LeftHandPinky1"),
    ("bot:jt_pinky2_L", "LeftHandPinky2"),
    ("bot:jt_pinky3_L", "LeftHandPinky3"),
]
for sb, pb in pairs:
    sp = M_full @ arm.data.bones[sb].head_local
    pp = pb_bl[pb]
    diff = sp - pp
    print(f"  {pb:18s}: Strongarm=({sp.x:+.3f},{sp.y:+.3f},{sp.z:+.3f}) | Prowl=({pp.x:+.3f},{pp.y:+.3f},{pp.z:+.3f}) | d=({diff.x:+.3f},{diff.y:+.3f},{diff.z:+.3f})")
