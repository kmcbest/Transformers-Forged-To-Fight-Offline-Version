import sys, os
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

sys.path.insert(0, r"E:\Agent\TFTF-blender")
import bpy
import json
import math
import numpy as np
from mathutils import Vector, Matrix
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
FBX_PATH = r"O:\agent\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"
DONOR_JSON = ROOT / "3rd-party-models" / "BlastOff" / "00_donor_reference" / "donor_summary.json"

from tools.blastoff.build_aligned_blastoff_robot import (
    BLASTOFF_MESH_NAMES,
    ROBOT_UV_MAP,
    remap_uvs_clean,
    load_megatronus_bones,
    pose_segment_world,
    pb_head_w,
    split_ue3_2shell_fingers,
    unity_to_blender
)

meg_pos = load_megatronus_bones()
print(f"Megatronus LeftArm in Blender: {meg_pos['LeftArm']}")
print(f"Megatronus LeftForeArm in Blender: {meg_pos['LeftForeArm']}")
print(f"Megatronus LeftHand in Blender: {meg_pos['LeftHand']}")
print(f"Megatronus LeftLeg in Blender: {meg_pos['LeftLeg']}")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=FBX_PATH)

arm = bpy.data.objects.get("Blast-off_ARM")
robot_objs = [bpy.data.objects[n] for n in BLASTOFF_MESH_NAMES if n in bpy.data.objects]

# Clean scene
keep_objs = set(robot_objs) | {arm}
for o in list(bpy.data.objects):
    if o not in keep_objs:
        bpy.data.objects.remove(o, do_unlink=True)

# 0. Center
RAW_OFFSET_Y = 10.0118
arm.location.y += RAW_OFFSET_Y
for obj in robot_objs:
    obj.location.y += RAW_OFFSET_Y
bpy.context.view_layer.update()

# 1. R_z(-90)
R_z90 = Matrix.Rotation(math.radians(-90), 4, 'Z')
arm.matrix_world = R_z90 @ arm.matrix_world
for obj in robot_objs:
    obj.matrix_world = R_z90 @ obj.matrix_world
bpy.context.view_layer.update()

bpy.ops.object.select_all(action="DESELECT")
for obj in robot_objs:
    obj.select_set(True)
arm.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# Scale
SCALE_BLASTOFF = 2.2928
arm.scale = (SCALE_BLASTOFF, SCALE_BLASTOFF, SCALE_BLASTOFF)
for obj in robot_objs:
    obj.scale = (SCALE_BLASTOFF, SCALE_BLASTOFF, SCALE_BLASTOFF)
bpy.ops.object.select_all(action="DESELECT")
for obj in robot_objs:
    obj.select_set(True)
arm.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# Split fingers
arml_obj = bpy.data.objects.get("RB_Blastoff_CHARSKEL_ArmLoL.001.dmx")
armr_obj = bpy.data.objects.get("RB_Blastoff_CHARSKEL_ArmLoR.001.dmx")
split_ue3_2shell_fingers(arm, arml_obj, side="L")
split_ue3_2shell_fingers(arm, armr_obj, side="R")

# Ensure Armature modifier is added to all mesh objects
for obj in robot_objs:
    arm_mod = obj.modifiers.get("Armature")
    if not arm_mod:
        arm_mod = obj.modifiers.new("Armature", "ARMATURE")
    arm_mod.object = arm

print(f"[+] Added Armature modifier to all {len(robot_objs)} robot mesh objects.")

# Pose Legs
bpy.ops.object.select_all(action="DESELECT")
arm.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode="POSE")

for side, sgn in (("L", 1.0), ("R", -1.0)):
    meg_side = "Left" if side == "L" else "Right"
    h_p = pb_head_w(arm, f"bip_hip_{side}")
    k_t = Vector((0.8965 * sgn, meg_pos[f"{meg_side}Leg"].y, meg_pos[f"{meg_side}Leg"].z))
    f_t = Vector((0.8965 * sgn, meg_pos[f"{meg_side}Foot"].y, meg_pos[f"{meg_side}Foot"].z))
    t_t = Vector((0.8965 * sgn, meg_pos[f"{meg_side}ToeBase"].y, meg_pos[f"{meg_side}ToeBase"].z))
    pose_segment_world(arm, f"bip_hip_{side}", f"bip_knee_{side}", Vector((0.8965 * sgn, h_p.y, h_p.z)), k_t, thickness_scale=0.96, preserve_length=False)
    pose_segment_world(arm, f"bip_knee_{side}", f"bip_foot_{side}", k_t, f_t, thickness_scale=0.96, preserve_length=False)
    pose_segment_world(arm, f"bip_foot_{side}", f"bip_toe_{side}", f_t, t_t, thickness_scale=0.96, preserve_length=True)

# Grounding check
bpy.ops.object.mode_set(mode="OBJECT")
deps = bpy.context.evaluated_depsgraph_get()
min_z = 999.0
for obj in robot_objs:
    ev = obj.evaluated_get(deps)
    em = ev.to_mesh()
    for v in em.vertices:
        wz = (ev.matrix_world @ v.co).z
        if wz < min_z:
            min_z = wz
    ev.to_mesh_clear()

print(f"min_z evaluated = {min_z:.4f}")
arm.location.z -= min_z
for obj in robot_objs:
    obj.location.z -= min_z
bpy.context.view_layer.update()

# Pose Torso & Arms
bpy.ops.object.select_all(action="DESELECT")
arm.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode="POSE")

pose_segment_world(arm, "bip_pelvis", "bip_spine_0", meg_pos["Hips"], meg_pos["Spine"], thickness_scale=1.0, preserve_length=False)
pose_segment_world(arm, "bip_spine_0", "bip_spine_1", meg_pos["Spine"], meg_pos["Spine1"], thickness_scale=1.0, preserve_length=False)
pose_segment_world(arm, "bip_spine_1", "bip_neck", meg_pos["Spine1"], meg_pos["Neck"], thickness_scale=1.0, preserve_length=False)
pose_segment_world(arm, "bip_neck", "bip_head", meg_pos["Neck"], meg_pos["Head"], thickness_scale=1.0, preserve_length=False)

for side, sgn in (("L", 1.0), ("R", -1.0)):
    meg_side = "Left" if side == "L" else "Right"
    ua_name = f"bip_upperArm_{side}"
    la_name = f"bip_lowerArm_{side}"
    h_name = f"bip_hand_{side}"

    ua_h = pb_head_w(arm, ua_name)
    wri_t = meg_pos[f"{meg_side}Hand"].copy()
    elb_t = meg_pos[f"{meg_side}ForeArm"].copy()
    arm_t = meg_pos[f"{meg_side}Arm"].copy()

    pose_segment_world(arm, ua_name, la_name, Vector((arm_t.x, ua_h.y, arm_t.z)), elb_t, thickness_scale=0.96, preserve_length=False)
    pose_segment_world(arm, la_name, h_name, elb_t, wri_t, thickness_scale=0.96, preserve_length=False)

print("[+] Arms posed.")

# Check bone positions of posed arm in Blender world coordinates:
for b in ["bip_lowerArm_L", "bip_lowerArm_R", "bip_knee_L", "bip_knee_R"]:
    pb = arm.pose.bones[b]
    hw = arm.matrix_world @ pb.head
    print(f"Posed bone {b:20s}: head world = ({hw.x:+.3f}, {hw.y:+.3f}, {hw.z:+.3f})")

# Check evaluated vertices for ArmLoL
bpy.ops.object.mode_set(mode="OBJECT")
deps = bpy.context.evaluated_depsgraph_get()
ev = arml_obj.evaluated_get(deps)
em = ev.to_mesh()
vs_x = [(ev.matrix_world @ v.co).x for v in em.vertices]
print(f"ArmLoL evaluated vertices X range: [{min(vs_x):.3f}, {max(vs_x):.3f}], mean = {sum(vs_x)/len(vs_x):.3f}")
ev.to_mesh_clear()
