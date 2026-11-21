import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import math
import bpy
from mathutils import Vector

FBX_SRC = r"e:\Agent\TFTF-blender\3rd-party-models\swoop\01_master\Swoop_pbr.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=FBX_SRC)

arm = bpy.data.objects.get("Bip001")
act = bpy.data.actions.get("Bip001|vehicle_idle01|Base Layer")
print(f"Action: {act.name}, frame_range: {act.frame_range}")

# Find which bones actually move across frames 1..58 in vehicle_idle01
arm.animation_data.action = act
bone_rot_ranges = {}
bone_loc_ranges = {}

for f in range(1, 59):
    bpy.context.scene.frame_set(f)
    bpy.context.view_layer.update()
    for pb in arm.pose.bones:
        q = pb.rotation_quaternion.copy()
        loc = pb.location.copy()
        bone_rot_ranges.setdefault(pb.name, []).append(q)
        bone_loc_ranges.setdefault(pb.name, []).append(loc)

print("\n=== Animated Bones in Bip001|vehicle_idle01|Base Layer (frames 1..58) ===")
for bname, quats in bone_rot_ranges.items():
    q0 = quats[0]
    max_ang = 0.0
    max_f = 1
    for idx, q in enumerate(quats):
        dot = min(1.0, max(-1.0, abs(q0.dot(q))))
        ang = math.degrees(2.0 * math.acos(dot))
        if ang > max_ang:
            max_ang = ang
            max_f = idx + 1
    locs = bone_loc_ranges[bname]
    l0 = locs[0]
    max_dist = max((l - l0).length for l in locs)
    if max_ang > 0.5 or max_dist > 0.001:
        print(f"  {bname:<28}: max_rot_delta = {max_ang:6.2f} deg (at frame {max_f:2d}), max_loc_delta = {max_dist:.4f}")

# Print detailed wing & body motion every 4 frames
tracked = [
    "Bip001 Pelvis", "Bip001 Spine", "Bip001 Spine1", "Back",
    "Bone_L_Wing_01(mirrored)", "Bone_L_Wing_02(mirrored)", "L_missile",
    "Bone_R_Wing_01", "Bone_R_Wing_02", "R_missile",
    "bird_neck", "bird_Head", "beak", "beak_the bottom",
    "Bip001 L Thigh", "Bone_L_Calf", "Bone_L_Foot00",
]
print("\n=== Frame-by-frame rotation deltas from Frame 1 (in degrees) ===")
header = "Frame | " + " | ".join(f"{b[:12]:>12}" for b in tracked if b in bone_rot_ranges)
print(header)
print("-" * len(header))
for f in range(1, 59, 3):
    row = [f"{f:5d}"]
    for b in tracked:
        if b not in bone_rot_ranges:
            continue
        q0 = bone_rot_ranges[b][0]
        q = bone_rot_ranges[b][f - 1]
        dot = min(1.0, max(-1.0, abs(q0.dot(q))))
        ang = math.degrees(2.0 * math.acos(dot))
        row.append(f"{ang:12.2f}")
    print(" | ".join(row))
