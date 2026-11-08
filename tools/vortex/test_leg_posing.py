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

bpy.ops.wm.open_mainfile(filepath=r"E:\Agent\TFTF-blender\3rd-party-models\vortex\vortex_master.blend")
arm = bpy.data.objects["Vortex_ARM"]
scale_factor = 2.05
arm.scale = (scale_factor, scale_factor, scale_factor)
arm.rotation_euler = (0, 0, math.radians(90.0))
bpy.context.view_layer.update()

bp_data = json.loads(Path(r"E:\Agent\TFTF-blender\tools\vortex\grindor_78_authoritative_bindposes.json").read_text(encoding="utf-8"))
g_b_pos = {}
for bname, info in bp_data.items():
    p = info["world_pos"]
    g_b_pos[bname] = mathutils.Vector((p["x"], p["z"], p["y"]))

def aim_bone_segment_world(arm_obj, parent_bname, child_bname, target_dir_world):
    bpy.context.view_layer.update()
    pb = arm_obj.pose.bones[parent_bname]
    pb_child = arm_obj.pose.bones[child_bname]
    p0 = (arm_obj.matrix_world @ pb.matrix).translation
    p1 = (arm_obj.matrix_world @ pb_child.matrix).translation
    cur_dir = (p1 - p0).normalized()
    tgt_dir = mathutils.Vector(target_dir_world).normalized()
    rot_diff = cur_dir.rotation_difference(tgt_dir).to_matrix().to_4x4()
    wmat = arm_obj.matrix_world @ pb.matrix
    pb.matrix = arm_obj.matrix_world.inverted() @ (mathutils.Matrix.Translation(p0) @ rot_diff @ mathutils.Matrix.Translation(-p0) @ wmat)
    bpy.context.view_layer.update()

# Aim thigh towards Grindor's knee
# Grindor LeftLeg vs LeftUpLeg:
thigh_dir_L = (g_b_pos["LeftLeg"] - g_b_pos["LeftUpLeg"]).normalized()
thigh_dir_R = (g_b_pos["RightLeg"] - g_b_pos["RightUpLeg"]).normalized()
calf_dir_L = (g_b_pos["LeftFoot"] - g_b_pos["LeftLeg"]).normalized()
calf_dir_R = (g_b_pos["RightFoot"] - g_b_pos["RightLeg"]).normalized()

print(f"Target Thigh dir L: {thigh_dir_L}")
print(f"Target Calf dir L:  {calf_dir_L}")

bpy.ops.object.mode_set(mode='POSE')
aim_bone_segment_world(arm, "bip_hip_L", "bip_knee_L", thigh_dir_L)
aim_bone_segment_world(arm, "bip_hip_R", "bip_knee_R", thigh_dir_R)
aim_bone_segment_world(arm, "bip_knee_L", "bip_foot_L", calf_dir_L)
aim_bone_segment_world(arm, "bip_knee_R", "bip_foot_R", calf_dir_R)

# Foot rotation to keep sole flat on ground
for bname, ang_deg in [("bip_foot_L", -4.0), ("bip_foot_R", 4.0)]:
    pb = arm.pose.bones[bname]
    p0 = (arm.matrix_world @ pb.matrix).translation
    rot_y = mathutils.Matrix.Rotation(math.radians(ang_deg), 4, 'Y')
    wmat = arm.matrix_world @ pb.matrix
    pb.matrix = arm.matrix_world.inverted() @ (mathutils.Matrix.Translation(p0) @ rot_y @ mathutils.Matrix.Translation(-p0) @ wmat)
    bpy.context.view_layer.update()

bpy.ops.object.mode_set(mode='OBJECT')

head_mesh = bpy.data.objects["RB_Vortex_CHARSKEL_Head.mo.dmx"]
deps = bpy.context.evaluated_depsgraph_get()
ev_mesh = head_mesh.evaluated_get(deps)
em = ev_mesh.to_mesh()
min_z = min((ev_mesh.matrix_world @ v.co).z for v in em.vertices)
ev_mesh.to_mesh_clear()
print(f"Posed Mesh min Z = {min_z:.4f}")
arm.location.z -= min_z
bpy.context.view_layer.update()

# Recheck ground contact after shift:
ev_mesh = head_mesh.evaluated_get(deps)
em = ev_mesh.to_mesh()
min_z_new = min((ev_mesh.matrix_world @ v.co).z for v in em.vertices)
ev_mesh.to_mesh_clear()
print(f"After grounding: Mesh min Z = {min_z_new:.4f} (ground contact!)")

# Check foot bone positions vs Grindor:
for b, gb in [("bip_foot_L", "LeftFoot"), ("bip_foot_R", "RightFoot")]:
    pb = arm.pose.bones[b]
    wpos = (arm.matrix_world @ pb.matrix).translation
    print(f"  Posed {b:12s}: ({wpos.x:6.3f}, {wpos.y:6.3f}, {wpos.z:6.3f}) | Grindor {gb}: ({g_b_pos[gb].x:6.3f}, {g_b_pos[gb].y:6.3f}, {g_b_pos[gb].z:6.3f})")
