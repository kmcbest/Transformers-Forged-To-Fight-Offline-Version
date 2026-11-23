import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
from pathlib import Path
import math
import os
import bpy
from mathutils import Vector, Matrix, Quaternion, Euler

ROOT = Path(r"E:\Agent\TFTF-blender")
SRC_DIR = ROOT / "3rd-party-models" / "Blitzwing_EW" / "01_source"
MEG_51_JSON = ROOT / "tools" / "blitzwing" / "megatron_51_authoritative_bindposes.json"
meg_51_data = json.loads(MEG_51_JSON.read_text(encoding="utf-8"))

def u_to_b(pos):
    return Vector((-float(pos[0]), -float(pos[2]), float(pos[1])))

meg_b_pos = {b: u_to_b(meg_51_data["bones"][b]["unity_world_pos"]) for b in meg_51_data["bones"]}

def pose_segment_world(arm_obj, bname, child_bname, target_head_w, target_end_w, thickness_scale=1.0, preserve_length=True):
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

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(SRC_DIR / "H_shandian_G1_M_LOD.fbx"))

mesh_obj = bpy.data.objects['H_shandian_G1_M_Lod']
arm_obj = bpy.data.objects['floor']

# Unparent
bpy.ops.object.select_all(action='DESELECT')
for o in [mesh_obj, arm_obj]:
    o.select_set(True)
bpy.context.view_layer.objects.active = arm_obj
bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
for o in list(bpy.data.objects):
    if o not in [mesh_obj, arm_obj]:
        bpy.data.objects.remove(o, do_unlink=True)

# Transform
arm_obj.rotation_euler = (0, 0, math.radians(-90))
mesh_obj.rotation_euler = (0, 0, math.radians(-90))
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.transform_apply(rotation=True)

min_z = min(v.co.z for v in mesh_obj.data.vertices)
mesh_obj.location.z -= min_z
arm_obj.location.z -= min_z
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

SCALE = 149.1728
mesh_obj.scale = (SCALE, SCALE, SCALE)
arm_obj.scale = (SCALE, SCALE, SCALE)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

mesh_obj.modifiers.clear()
mesh_obj.parent = arm_obj
arm_mod = mesh_obj.modifiers.new("Armature", "ARMATURE")
arm_mod.object = arm_obj

bpy.context.view_layer.objects.active = arm_obj
bpy.ops.object.mode_set(mode='POSE')

# Pose arms with preserve_length=True
for side, pfx in [("L", "Left"), ("R", "Right")]:
    sh_head = (arm_obj.matrix_world @ arm_obj.pose.bones[f"Bip001 {side} UpperArm"].matrix).translation.copy()
    elbow_targ = meg_b_pos[f"{pfx}ForeArm"]
    wrist_targ = meg_b_pos[f"{pfx}Hand"]

    pose_segment_world(arm_obj, f"Bip001 {side} UpperArm", f"Bip001 {side} Forearm", sh_head, elbow_targ, thickness_scale=1.0, preserve_length=True)
    pose_segment_world(arm_obj, f"Bip001 {side} Forearm", f"Bip001 {side} Hand", elbow_targ, wrist_targ, thickness_scale=1.0, preserve_length=True)

# Pre-curl fists on BOTH sides (Track B)
# For Left Hand:
# Fingers 1..4 curl inward around local Z with negative angle (-50 to -65 deg)
for fi in range(1, 5):
    pb0 = arm_obj.pose.bones[f"Bip001 L Finger{fi}"]
    pb1 = arm_obj.pose.bones[f"Bip001 L Finger{fi}1"]
    pb2 = arm_obj.pose.bones[f"Bip001 L Finger{fi}2"]
    for pb, ang in [(pb0, -55.0), (pb1, -65.0), (pb2, -55.0)]:
        if pb:
            pb.rotation_mode = 'XYZ'
            pb.rotation_euler = Euler((0, 0, math.radians(ang)), 'XYZ')

# Left Thumb: curl across palm
pb_t0 = arm_obj.pose.bones["Bip001 L Finger0"]
pb_t1 = arm_obj.pose.bones["Bip001 L Finger01"]
pb_t2 = arm_obj.pose.bones["Bip001 L Finger02"]
if pb_t0:
    pb_t0.rotation_mode = 'XYZ'
    pb_t0.rotation_euler = Euler((math.radians(25), 0, math.radians(40)), 'XYZ')
if pb_t1:
    pb_t1.rotation_mode = 'XYZ'
    pb_t1.rotation_euler = Euler((0, 0, math.radians(45)), 'XYZ')
if pb_t2:
    pb_t2.rotation_mode = 'XYZ'
    pb_t2.rotation_euler = Euler((0, 0, math.radians(40)), 'XYZ')

# For Right Hand:
# Fingers 1..4 curl inward around local Z
for fi in range(1, 5):
    pb0 = arm_obj.pose.bones[f"Bip001 R Finger{fi}"]
    pb1 = arm_obj.pose.bones[f"Bip001 R Finger{fi}1"]
    pb2 = arm_obj.pose.bones[f"Bip001 R Finger{fi}2"]
    for pb, ang in [(pb0, -55.0), (pb1, -65.0), (pb2, -55.0)]:
        if pb:
            pb.rotation_mode = 'XYZ'
            pb.rotation_euler = Euler((0, 0, math.radians(ang)), 'XYZ')

# Right Thumb:
pb_rt0 = arm_obj.pose.bones["Bip001 R Finger0"]
pb_rt1 = arm_obj.pose.bones["Bip001 R Finger01"]
pb_rt2 = arm_obj.pose.bones["Bip001 R Finger02"]
if pb_rt0:
    pb_rt0.rotation_mode = 'XYZ'
    pb_rt0.rotation_euler = Euler((math.radians(-25), 0, math.radians(-40)), 'XYZ')
if pb_rt1:
    pb_rt1.rotation_mode = 'XYZ'
    pb_rt1.rotation_euler = Euler((0, 0, math.radians(-45)), 'XYZ')
if pb_rt2:
    pb_rt2.rotation_mode = 'XYZ'
    pb_rt2.rotation_euler = Euler((0, 0, math.radians(-40)), 'XYZ')

bpy.context.view_layer.update()
print("[✓] Posed arms & curled fists successfully!")

# Apply armature modifier to freeze this geometry
bpy.ops.object.mode_set(mode='OBJECT')
bpy.context.view_layer.objects.active = mesh_obj
mesh_obj.select_set(True)
bpy.ops.object.modifier_apply(modifier="Armature")
mesh_obj.parent = None
bpy.data.objects.remove(arm_obj, do_unlink=True)
print("[✓] Armature modifier applied to mesh!")

# Setup material and render preview
tex_path = SRC_DIR / "H_shandian_G1_M_T_a.png"
mat = bpy.data.materials.new(name="cha_blitzwing_test")
mat.use_nodes = True
nodes = mat.node_tree.nodes
links = mat.node_tree.links
nodes.clear()

output = nodes.new("ShaderNodeOutputMaterial")
output.location = (600, 0)
bsdf = nodes.new("ShaderNodeBsdfPrincipled")
bsdf.location = (200, 0)
links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

if tex_path.exists():
    tex_node = nodes.new("ShaderNodeTexImage")
    tex_node.image = bpy.data.images.load(str(tex_path))
    links.new(tex_node.outputs["Color"], bsdf.inputs["Base Color"])

mesh_obj.data.materials.clear()
mesh_obj.data.materials.append(mat)
for poly in mesh_obj.data.polygons:
    poly.material_index = 0

# Find Left Hand vertex positions
vg = mesh_obj.vertex_groups.get("Bip001 L Hand")
v_indices = [v.index for v in mesh_obj.data.vertices if any(g.group == vg.index for g in v.groups)]
hand_center = sum((mesh_obj.data.vertices[i].co for i in v_indices), Vector((0,0,0))) / max(len(v_indices), 1)
print(f"Hand center: {hand_center}")

cam_data = bpy.data.cameras.new("CamHand")
cam_obj = bpy.data.objects.new("CamHand", cam_data)
bpy.context.scene.collection.objects.link(cam_obj)
bpy.context.scene.camera = cam_obj

cam_obj.location = hand_center + Vector((1.5, -1.8, 0.5))
rot_q = (hand_center - cam_obj.location).to_track_quat('-Z', 'Y')
cam_obj.rotation_euler = rot_q.to_euler()

light_data = bpy.data.lights.new(name="Sun", type='SUN')
light_data.energy = 4.0
light_obj = bpy.data.objects.new(name="Sun", object_data=light_data)
bpy.context.scene.collection.objects.link(light_obj)
light_obj.location = hand_center + Vector((2, -2, 3))
light_obj.rotation_euler = (math.radians(45), 0, math.radians(45))

bpy.context.scene.render.engine = 'BLENDER_EEVEE'
bpy.context.scene.render.resolution_x = 1000
bpy.context.scene.render.resolution_y = 1000
out_img = ROOT / "renders/blitzwing/fist_preview.png"
bpy.context.scene.render.filepath = str(out_img)
bpy.ops.render.render(write_still=True)
print(f"Saved: {out_img}")
