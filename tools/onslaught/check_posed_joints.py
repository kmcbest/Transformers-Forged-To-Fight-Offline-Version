import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
import math
from pathlib import Path
import bpy
import mathutils

ROOT = Path(r"E:\Agent\TFTF-blender")
BONES_JSON = ROOT / "tools" / "demolishor" / "ironhide_80_bones.json"
MASTER_BLEND = ROOT / "3rd-party-models" / "onslaught" / "onslaught_master.blend"

bpy.ops.wm.open_mainfile(filepath=str(MASTER_BLEND))
ons_arm = bpy.data.objects["Onslaught_ARM"]
scale_factor = 1.725
ons_arm.scale = (scale_factor, scale_factor, scale_factor)
ons_arm.rotation_euler = (0.0, 0.0, math.radians(90.0))
bpy.context.view_layer.update()

bpy.ops.object.select_all(action='DESELECT')
ons_arm.select_set(True)
bpy.context.view_layer.objects.active = ons_arm
bpy.ops.object.mode_set(mode='POSE')

def aim_bone_segment_world(arm_obj, parent_bname, child_bname, target_dir_world):
    bpy.context.view_layer.update()
    pb = arm_obj.pose.bones[parent_bname]
    pb_child = arm_obj.pose.bones[child_bname]
    p0 = (arm_obj.matrix_world @ pb.matrix).translation
    p1 = (arm_obj.matrix_world @ pb_child.matrix).translation
    cur_dir = (p1 - p0).normalized()
    tgt_dir = mathutils.Vector(target_dir_world).normalized()
    rot_diff = cur_dir.rotation_difference(tgt_dir).to_matrix().to_4x4()
    world_mat = arm_obj.matrix_world @ pb.matrix
    new_world = mathutils.Matrix.Translation(p0) @ rot_diff @ mathutils.Matrix.Translation(-p0) @ world_mat
    pb.matrix = arm_obj.matrix_world.inverted() @ new_world
    bpy.context.view_layer.update()

aim_bone_segment_world(ons_arm, "bip_upperArm_L", "bip_lowerArm_L", (-0.168, 0.02, -0.985))
aim_bone_segment_world(ons_arm, "bip_upperArm_R", "bip_lowerArm_R", (0.168, 0.02, -0.985))
aim_bone_segment_world(ons_arm, "bip_lowerArm_L", "bip_hand_L", (-0.01, 0.04, -0.999))
aim_bone_segment_world(ons_arm, "bip_lowerArm_R", "bip_hand_R", (0.01, 0.04, -0.999))
aim_bone_segment_world(ons_arm, "bip_hip_L", "bip_knee_L", (-0.068, 0.02, -0.997))
aim_bone_segment_world(ons_arm, "bip_hip_R", "bip_knee_R", (0.068, 0.02, -0.997))
aim_bone_segment_world(ons_arm, "bip_knee_L", "bip_foot_L", (-0.060, -0.08, -0.995))
aim_bone_segment_world(ons_arm, "bip_knee_R", "bip_foot_R", (0.060, -0.08, -0.995))
bpy.ops.object.mode_set(mode='OBJECT')

# Compute grounding shift min_z on Legs
depsgraph = bpy.context.evaluated_depsgraph_get()
legs_eval = bpy.data.objects["RB_Onslaught_CHARSKEL_Legs.mo.dmx"].evaluated_get(depsgraph)
m = legs_eval.to_mesh()
min_z = min((legs_eval.matrix_world @ v.co).z for v in m.vertices)
legs_eval.to_mesh_clear()

with open(BONES_JSON, "r", encoding="utf-8") as f:
    ih = json.load(f)["bones"]

def ih_pos(nm):
    t = mathutils.Matrix(ih[nm]["matrix"]).to_translation()
    return mathutils.Vector((t.x, t.z, t.y))

pairs = [
    ("bip_upperArm_L", "LeftArm"),
    ("bip_lowerArm_L", "LeftForeArm"),
    ("bip_hand_L", "LeftHand"),
    ("bip_thumb_0_L", "LeftHandThumb1"),
    ("bip_thumb_1_L", "LeftHandThumb2"),
    ("bip_index_0_L", "LeftHandIndex1"),
    ("bip_index_1_L", "LeftHandIndex2"),
    ("bip_middle_0_L", "LeftHandMiddle1"),
    ("bip_middle_1_L", "LeftHandMiddle2"),
    ("bip_ring_0_L", "LeftHandRing1"),
    ("bip_ring_1_L", "LeftHandRing2"),
    ("bip_pinky_0_L", "LeftHandPinky1"),
    ("bip_pinky_1_L", "LeftHandPinky2"),
    ("bip_hip_L", "LeftUpLeg"),
    ("bip_knee_L", "LeftLeg"),
    ("bip_foot_L", "LeftFoot"),
]
print(f"Grounding shift -min_z = {-min_z:.3f}m")
for foc_nm, ih_nm in pairs:
    fp = (ons_arm.matrix_world @ ons_arm.pose.bones[foc_nm].matrix).translation - mathutils.Vector((0, 0, min_z))
    ip = ih_pos(ih_nm)
    diff = fp - ip
    print(f"  {foc_nm:18s} ({fp.x:6.3f},{fp.y:6.3f},{fp.z:6.3f}) vs {ih_nm:18s} ({ip.x:6.3f},{ip.y:6.3f},{ip.z:6.3f}) | diff=({diff.x:+6.3f},{diff.y:+6.3f},{diff.z:+6.3f})")
