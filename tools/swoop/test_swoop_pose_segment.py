import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
import math
from pathlib import Path
import bpy
from mathutils import Matrix, Vector, Quaternion

# 1. Load Ramjet authoritative bindposes
with open("tools/swoop/ramjet_78_authoritative_bindposes.json", "r", encoding="utf-8") as f:
    donor_data = json.load(f)

donor_bones = donor_data["bones"]
donor_blender_pos = {}
for bname, binfo in donor_bones.items():
    ux, uy, uz = binfo["unity_world_pos"]
    # Unity (ux, uy, uz) to Blender (bx=-ux, by=-uz, bz=uy)
    donor_blender_pos[bname] = Vector((-ux, -uz, uy))

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath="3rd-party-models/swoop/01_master/Swoop_pbr.fbx")

arm = bpy.data.objects.get("Bip001")
swoop = bpy.data.objects.get("Swoop.001")

# Clear unneeded objects
for o in list(bpy.data.objects):
    if o.name in ["Symbol_DC", "Shadow", "Swoop_Weapon"] or o.type == 'EMPTY':
        bpy.data.objects.remove(o, do_unlink=True)

# Start from idle01 frame 1
act = bpy.data.actions.get("Bip001|idle01|Base Layer")
if act and arm.animation_data:
    arm.animation_data.action = act
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()

# Unparent arm and swoop keeping world matrix
for o in [arm, swoop]:
    mw = o.matrix_world.copy()
    o.parent = None
    o.matrix_world = mw

# Measure current height and scale factor
depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj = swoop.evaluated_get(depsgraph)
eval_mesh = eval_obj.to_mesh()
zs = [v.co.z for v in eval_mesh.vertices]
eval_obj.to_mesh_clear()
raw_h = max(zs) - min(zs)
scale_factor = 11.40 / raw_h
print(f"Raw height: {raw_h:.4f}m, scale factor: {scale_factor:.4f}")

# Scale arm and swoop by scale_factor
S_mat = Matrix.Scale(scale_factor, 4)
arm.matrix_world = S_mat @ arm.matrix_world
swoop.matrix_world = S_mat @ swoop.matrix_world

bpy.context.view_layer.update()

# Grounding: find lowest foot Z and offset arm & swoop
depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj = swoop.evaluated_get(depsgraph)
eval_mesh = eval_obj.to_mesh()
min_z = min(v.co.z for v in eval_mesh.vertices)
eval_obj.to_mesh_clear()
print(f"Lowest Z before grounding: {min_z:.4f}m")
arm.location.z -= min_z
swoop.location.z -= min_z
bpy.context.view_layer.update()

# Define pose_segment_world helper
def pose_segment_world(arm_obj, bname, child_bname, target_head_w, target_end_w, thickness_scale=1.0, preserve_length=False):
    bpy.context.view_layer.update()
    pb = arm_obj.pose.bones[bname]
    pb_child = arm_obj.pose.bones[child_bname]
    w_old = arm_obj.matrix_world @ pb.matrix
    curr_head = w_old.translation.copy()
    curr_end = (arm_obj.matrix_world @ pb_child.matrix).translation.copy()

    v_curr = curr_end - curr_head
    v_targ = target_end_w - target_head_w
    len_curr = v_curr.length
    len_targ = v_targ.length

    q_rot = v_curr.rotation_difference(v_targ) if (len_curr > 1e-5 and len_targ > 1e-5) else Quaternion()
    s_len = 1.0 if preserve_length else min(1.35, max(0.70, (len_targ / len_curr) if len_curr > 1e-5 else 1.0))

    d = v_curr.normalized() if len_curr > 1e-5 else Vector((0, 0, -1))
    S = Matrix.Identity(3) * thickness_scale
    for r in range(3):
        for c in range(3):
            S[r][c] += (s_len - thickness_scale) * d[r] * d[c]

    R_new = q_rot.to_matrix() @ S @ w_old.to_3x3()
    M_new_w = R_new.to_4x4()
    M_new_w.translation = target_head_w
    pb.matrix = arm_obj.matrix_world.inverted() @ M_new_w
    bpy.context.view_layer.update()

# Pose key segments to match Ramjet's authoritative bindposes!
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='POSE')

# Left Arm
pose_segment_world(arm, "Bone_L_UpperArm", "Bone_L_Forearm", donor_blender_pos["LeftArm"], donor_blender_pos["LeftForeArm"])
pose_segment_world(arm, "Bone_L_Forearm", "Bone_L_Hand", donor_blender_pos["LeftForeArm"], donor_blender_pos["LeftHand"])

# Right Arm
pose_segment_world(arm, "Bone_R_UpperArm", "Bone_R_Forearm", donor_blender_pos["RightArm"], donor_blender_pos["RightForeArm"])
pose_segment_world(arm, "Bone_R_Forearm", "Bone_R_Hand", donor_blender_pos["RightForeArm"], donor_blender_pos["RightHand"])

# Left Leg
pose_segment_world(arm, "Bone_L_Thigh", "Bone_L_Calf", donor_blender_pos["LeftUpLeg"], donor_blender_pos["LeftLeg"])
pose_segment_world(arm, "Bone_L_Calf", "Bone_L_Foot00", donor_blender_pos["LeftLeg"], donor_blender_pos["LeftFoot"])

# Right Leg
pose_segment_world(arm, "Bone_R_Thigh", "Bone_R_Calf", donor_blender_pos["RightUpLeg"], donor_blender_pos["RightLeg"])
pose_segment_world(arm, "Bone_R_Calf", "Bone_R_Foot00", donor_blender_pos["RightLeg"], donor_blender_pos["RightFoot"])

bpy.ops.object.mode_set(mode='OBJECT')
bpy.context.view_layer.update()

# Bake evaluated mesh for Swoop
depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj = swoop.evaluated_get(depsgraph)
eval_mesh = bpy.data.meshes.new_from_object(eval_obj)

baked_swoop = bpy.data.objects.new("cha_swoop_robot_aligned", eval_mesh)
bpy.context.scene.collection.objects.link(baked_swoop)
baked_swoop.matrix_world = eval_obj.matrix_world

# Copy vertex groups
for vg in swoop.vertex_groups:
    baked_swoop.vertex_groups.new(name=vg.name)
    for v in swoop.data.vertices:
        for g in v.groups:
            if g.group == vg.index:
                baked_swoop.vertex_groups[vg.name].add([v.index], g.weight, 'REPLACE')

bpy.context.view_layer.objects.active = baked_swoop
bpy.ops.object.select_all(action='DESELECT')
baked_swoop.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# Audit bounds and axis parity
xs = [v.co.x for v in baked_swoop.data.vertices]
ys = [v.co.y for v in baked_swoop.data.vertices]
zs = [v.co.z for v in baked_swoop.data.vertices]
print(f"Aligned Swoop Robot Bounds:")
print(f"  X: [{min(xs):.3f}, {max(xs):.3f}] (span: {max(xs)-min(xs):.3f}m)")
print(f"  Y: [{min(ys):.3f}, {max(ys):.3f}] (span: {max(ys)-min(ys):.3f}m)")
print(f"  Z: [{min(zs):.3f}, {max(zs):.3f}] (span: {max(zs)-min(zs):.3f}m)")

def vg_mean_x(name):
    vg = baked_swoop.vertex_groups.get(name)
    if not vg: return None
    pts = [v.co.x for v in baked_swoop.data.vertices if any(g.group == vg.index and g.weight > 0.4 for g in v.groups)]
    return sum(pts) / len(pts) if pts else None

print(f"Axis Audit:")
print(f"  Left Hand mean X:  {vg_mean_x('Bone_L_Hand'):+.3f}m (must be > +0.5)")
print(f"  Right Hand mean X: {vg_mean_x('Bone_R_Hand'):+.3f}m (must be < -0.5)")
print(f"  Left Arm mean X:   {vg_mean_x('Bone_L_UpperArm'):+.3f}m (must be > +0.5)")
print(f"  Right Arm mean X:  {vg_mean_x('Bone_R_UpperArm'):+.3f}m (must be < -0.5)")
print(f"  Left Foot mean X:  {vg_mean_x('Bone_L_Foot00'):+.3f}m (must be > +0.5)")
print(f"  Right Foot mean X: {vg_mean_x('Bone_R_Foot00'):+.3f}m (must be < -0.5)")

# Render front view
mat = bpy.data.materials.new("M_Aligned_Preview")
mat.use_nodes = True
bsdf = mat.node_tree.nodes.get("Principled BSDF")
tex_node = mat.node_tree.nodes.new("ShaderNodeTexImage")
tex_node.image = bpy.data.images.load("e:/Agent/TFTF-blender/3rd-party-models/swoop/01_master/textures/Tx_Swoop_D_RGB.png")
mat.node_tree.links.new(tex_node.outputs["Color"], bsdf.inputs["Base Color"])
baked_swoop.data.materials.append(mat)

# Hide original objects from render
arm.hide_render = True
swoop.hide_render = True

cam_data = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_data)
bpy.context.scene.collection.objects.link(cam)
cam.location = Vector((0, -22, 5.7))
cam.rotation_euler = (1.5708, 0, 0)
bpy.context.scene.camera = cam

light_data = bpy.data.lights.new("Sun", type='SUN')
light_data.energy = 4.0
light = bpy.data.objects.new("Sun", light_data)
bpy.context.scene.collection.objects.link(light)
light.rotation_euler = (0.785, 0.5, 0)

bpy.context.scene.render.resolution_x = 1024
bpy.context.scene.render.resolution_y = 1024
bpy.context.scene.render.filepath = "e:/Agent/TFTF-blender/renders/swoop/swoop_aligned_pose_preview.png"
bpy.ops.render.render(write_still=True)
print("Rendered swoop_aligned_pose_preview.png")
