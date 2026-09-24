# -*- coding: utf-8 -*-
"""
build_aligned_demolishor.py

Properly aligns Demolishor with Ironhide in 3D space:
1. Scales Demolishor by 1.775 (to height 10.42m).
2. Rotates Demolishor by +90 deg around Z to face forward.
3. Builds the 80-bone Armature with proper Unity->Blender coordinate conversion.
4. Remaps vertex groups to the 80 bones.
5. Exports the rigged FBX to unity_build_project.
"""

import sys
import json
import math
from pathlib import Path
import bpy
import mathutils

print("=== Starting Aligned Demolishor Rigging ===")

bpy.ops.wm.read_factory_settings(use_empty=True)

# 1. Load the 80 bones data
with open("tools/demolishor/ironhide_80_bones.json", "r", encoding="utf-8") as f:
    bones_data = json.load(f)

bone_order = bones_data["bone_order"]
bones_dict = bones_data["bones"]

# 2. Convert Unity bone matrix to Blender edit bone coordinates
# Unity: X=Right, Y=Up, Z=Forward
# Blender: X=Right, Y=Forward, Z=Up
# Transformation: x_b = x_u, y_b = z_u, z_b = y_u
def unity_pos_to_blender(u_vec):
    return mathutils.Vector((u_vec[0], u_vec[2], u_vec[1]))

# 3. Create Armature
arm_data = bpy.data.armatures.new("character_model")
arm_obj = bpy.data.objects.new("character_model", arm_data)
bpy.context.scene.collection.objects.link(arm_obj)
bpy.context.view_layer.objects.active = arm_obj
bpy.ops.object.mode_set(mode='EDIT')

edit_bones = {}

# Pass 1: create edit bones and set heads
for name in bone_order:
    b_info = bones_dict[name]
    mat = mathutils.Matrix(b_info["matrix"])
    u_head = mat.to_translation()
    b_head = unity_pos_to_blender(u_head)
    
    eb = arm_data.edit_bones.new(name)
    eb.head = b_head
    eb.tail = b_head + mathutils.Vector((0, 0, 0.1))
    edit_bones[name] = eb

# Pass 2: set parents and orient tails
for name in bone_order:
    b_info = bones_dict[name]
    parent_name = b_info.get("parent")
    eb = edit_bones[name]
    if parent_name and parent_name in edit_bones:
        eb.parent = edit_bones[parent_name]
        p_eb = edit_bones[parent_name]
        diff = eb.head - p_eb.head
        if diff.length > 0.05:
            p_eb.tail = eb.head

# Ensure minimum tail length
for eb in arm_data.edit_bones:
    if (eb.tail - eb.head).length < 0.01:
        eb.tail = eb.head + mathutils.Vector((0, 0, 0.1))

bpy.ops.object.mode_set(mode='OBJECT')
print(f"[✓] Created Armature with {len(arm_obj.data.bones)} bones matching Ironhide!")

# 4. Import Demolishor FBX
fbx_path = r"d:\Agent\tftf\3rd-party-models\transformers-fall-of-cybertron-demolishor\source\transformers fall of cybertron Demolishor.fbx"
bpy.ops.import_scene.fbx(filepath=fbx_path)

demolishor_arm = bpy.data.objects.get("Demolishor_ARM")
demolishor_mesh = bpy.data.objects.get("RB_DemolishorWeaponArm_SKEL.mo.dmx")

for obj in list(bpy.data.objects):
    if obj not in [arm_obj, demolishor_mesh, demolishor_arm]:
        bpy.data.objects.remove(obj, do_unlink=True)

# 5. Scale and Rotate Demolishor Mesh to match Ironhide
scale_factor = 1.775
print(f"[*] Scaling Demolishor mesh by {scale_factor}...")
demolishor_mesh.scale = (scale_factor, scale_factor, scale_factor)
bpy.context.view_layer.objects.active = demolishor_mesh
bpy.ops.object.transform_apply(scale=True)

print("[*] Rotating Demolishor mesh by +90 deg around Z to align facing...")
demolishor_mesh.rotation_euler = (0, 0, math.radians(90))
bpy.ops.object.transform_apply(rotation=True)

# Align height so boots touch ground at Z = 0 (no +0.45m stretch!)
min_z = min(v.co.z for v in demolishor_mesh.data.vertices)
print(f"[*] Grounding boots to Z = 0 (offset: {-min_z:.3f}m)...")
demolishor_mesh.location.z -= min_z
bpy.ops.object.transform_apply(location=True)

# Apply brawler combat stance: 8.0 deg leg outward splay, leveled boots, +18 deg forearm poise
print("[*] Applying brawler combat stance: 8.0 deg leg outward splay, leveled boots, +18 deg forearm poise...")
angle = 8.0
rot_l = mathutils.Matrix.Rotation(math.radians(angle), 4, 'Y')
rot_r = mathutils.Matrix.Rotation(math.radians(-angle), 4, 'Y')
rot_l_level = mathutils.Matrix.Rotation(math.radians(-angle), 4, 'Y')
rot_r_level = mathutils.Matrix.Rotation(math.radians(angle), 4, 'Y')
rot_l_yaw = mathutils.Matrix.Rotation(math.radians(angle), 4, 'Z')
rot_r_yaw = mathutils.Matrix.Rotation(math.radians(-angle), 4, 'Z')

l_hip_pivot = mathutils.Vector((-0.85, -0.1, 4.8))
r_hip_pivot = mathutils.Vector((0.85, -0.1, 4.8))

l_leg_vgs = [vg.index for vg in demolishor_mesh.vertex_groups if any(k in vg.name for k in ["L_Leg", "L_Thigh", "L_Knee"])]
r_leg_vgs = [vg.index for vg in demolishor_mesh.vertex_groups if any(k in vg.name for k in ["R_Leg", "R_Thigh", "R_Knee"])]
l_foot_vgs = [vg.index for vg in demolishor_mesh.vertex_groups if any(k in vg.name for k in ["L_Leg03", "L_Leg04"])]
r_foot_vgs = [vg.index for vg in demolishor_mesh.vertex_groups if any(k in vg.name for k in ["R_Leg03", "R_Leg04"])]

for v in demolishor_mesh.data.vertices:
    if any(g.group in l_leg_vgs and g.weight > 0.3 for g in v.groups):
        v.co = l_hip_pivot + (rot_l @ (v.co - l_hip_pivot))
    elif any(g.group in r_leg_vgs and g.weight > 0.3 for g in v.groups):
        v.co = r_hip_pivot + (rot_r @ (v.co - r_hip_pivot))

l_foot_pts = [v.co for v in demolishor_mesh.data.vertices if any(g.group in l_foot_vgs and g.weight > 0.3 for g in v.groups)]
if l_foot_pts:
    p = sum(l_foot_pts, mathutils.Vector((0, 0, 0))) / len(l_foot_pts)
    for v in demolishor_mesh.data.vertices:
        if any(g.group in l_foot_vgs and g.weight > 0.3 for g in v.groups):
            v.co = p + (rot_l_yaw @ (rot_l_level @ (v.co - p)))

r_foot_pts = [v.co for v in demolishor_mesh.data.vertices if any(g.group in r_foot_vgs and g.weight > 0.3 for g in v.groups)]
if r_foot_pts:
    p = sum(r_foot_pts, mathutils.Vector((0, 0, 0))) / len(r_foot_pts)
    for v in demolishor_mesh.data.vertices:
        if any(g.group in r_foot_vgs and g.weight > 0.3 for g in v.groups):
            v.co = p + (rot_r_yaw @ (rot_r_level @ (v.co - p)))

# Forearms tilt forward by +18 deg
rot_forearm = mathutils.Matrix.Rotation(math.radians(18.0), 4, 'X')
l_elbow_pivot = mathutils.Vector((-3.26, -0.45, 6.50))
r_elbow_pivot = mathutils.Vector((3.35, -0.31, 6.52))

l_forearm_vgs = [vg.index for vg in demolishor_mesh.vertex_groups if any(k in vg.name for k in ["L_Arm03", "L_Arm04", "L_Elbow", "L_Finger"])]
r_forearm_vgs = [vg.index for vg in demolishor_mesh.vertex_groups if any(k in vg.name for k in ["R_Arm03", "R_Arm04", "R_Elbow", "R_Finger"])]

for v in demolishor_mesh.data.vertices:
    if any(g.group in l_forearm_vgs and g.weight > 0.3 for g in v.groups):
        v.co = l_elbow_pivot + (rot_forearm @ (v.co - l_elbow_pivot))
    elif any(g.group in r_forearm_vgs and g.weight > 0.3 for g in v.groups):
        v.co = r_elbow_pivot + (rot_forearm @ (v.co - r_elbow_pivot))

# Re-ground boots firmly to Z = 0
min_z = min(v.co.z for v in demolishor_mesh.data.vertices)
demolishor_mesh.location.z -= min_z
bpy.ops.object.transform_apply(location=True)

# 6. Bone mapping (100% comprehensive coverage of all 79 vertex groups)
BONE_MAPPING = {
    # Spine & Pelvis
    "C_Root_Reference_XR": "Hips",
    "C_Spine00_Hips_XB": "Hips",
    "C_Spine01_Lumbar01_XB": "Spine",
    "C_Spine02_Lumbar02_XB": "Spine1",
    "C_Lumbar02Robo01_XT": "Spine1",
    "C_Lumbar02Robo02_XT": "Spine1",
    "C_Lumbar02Robo03_XT": "Spine1",
    "C_Lumbar02Robo04_XT": "Spine1",
    "C_Lumbar02Robo05_XT": "Spine1",
    "L_Lumbar02Robo01_XT": "Spine1",
    "L_Lumbar02Robo02_XT": "Spine1",
    "L_Lumbar02Robo03_XT": "Spine1",
    "L_Lumbar02Robo04_XT": "Spine1",
    "L_Lumbar02Robo05_XT": "Spine1",
    "L_Lumbar02Robo06_XT": "Spine1",
    "L_Lumbar02Robo07_XT": "Spine1",
    "L_Lumbar02Robo08_XT": "Spine1",
    "R_Lumbar02Robo01_XT": "Spine1",
    "R_Lumbar02Robo02_XT": "Spine1",
    "R_Lumbar02Robo04_XT": "Spine1",
    "R_Lumbar02Robo05_XT": "Spine1",
    "R_Lumbar02Robo06_XT": "Spine1",
    "R_Lumbar02Robo07_XT": "Spine1",
    "R_Lumbar02Robo08_XT": "Spine1",

    # Head & Neck & Face (Correctly mapped to Head/Neck/Jaw)
    "C_Spine03_Neck01_XB": "Neck",
    "C_Head01_Neck_XB": "Neck",
    "C_Spine04_Head_XB": "Head",
    "C_Head01_Face_XF2": "Head",
    "C_Head02_Head_XB": "Head",
    "C_Face01_Jaw_XF2": "Jaw",

    # Left Arm & Shoulder
    "L_Arm01_Clav_XB": "LeftShoulder",
    "L_Arm02_Shoulder_XB": "LeftArm",
    "L_ShoulderRobo01_XT": "LeftArm",
    "L_ShoulderRobo02_XT": "LeftArm",
    "L_Arm03_Elbow_XB": "LeftForeArm",
    "L_ElbowRobo01_XT": "LeftForeArm",
    "L_ElbowRobo02_XT": "LeftForeArm",
    "L_Arm04_Hand_XB": "LeftHand",

    # Left Hand Fingers (Merged solidly into LeftHand to eliminate stray floating chunks)
    "L_Finger01_Thumb01_XL2": "LeftHand",
    "L_Finger01_Thumb02_XL2": "LeftHand",
    "L_Finger02_Index01_XL2": "LeftHand",
    "L_Finger02_Index02_XL2": "LeftHand",
    "L_Finger03_Middle01_XL2": "LeftHand",
    "L_Finger03_Middle02_XL2": "LeftHand",
    "L_Finger04_Ring01_XL2": "LeftHand",
    "L_Finger04_Ring02_XL2": "LeftHand",
    "L_Finger05_Pinky01_XL2": "LeftHand",
    "L_Finger05_Pinky02_XL2": "LeftHand",

    # Right Arm & Shoulder
    "R_Arm01_Clav_XB": "RightShoulder",
    "R_Arm02_Shoulder_XB": "RightArm",
    "R_ShoulderRobo01_XT": "RightArm",
    "R_ShoulderRobo02_XT": "RightArm",
    "R_Arm03_Elbow_XB": "RightForeArm",
    "R_ElbowRobo01_XT": "RightForeArm",
    "R_Arm04_Hand_XB": "RightHand",

    # Right Hand Fingers (Merged solidly into RightHand to eliminate stray floating chunks)
    "R_Finger01_Thumb01_XL2": "RightHand",
    "R_Finger01_Thumb02_XL2": "RightHand",
    "R_Finger02_Index01_XL2": "RightHand",
    "R_Finger02_Index02_XL2": "RightHand",
    "R_Finger03_Middle01_XL2": "RightHand",
    "R_Finger03_Middle02_XL2": "RightHand",
    "R_Finger04_Ring01_XL2": "RightHand",
    "R_Finger04_Ring02_XL2": "RightHand",
    "R_Finger05_Pinky01_XL2": "RightHand",
    "R_Finger05_Pinky02_XL2": "RightHand",

    # Left Leg & Foot (Toes merged into LeftFoot for solid grounded foot base)
    "L_Leg01_Thigh_XB": "LeftUpLeg",
    "L_ThighRobo01_XT": "LeftUpLeg",
    "L_ThighRobo02_XT": "LeftUpLeg",
    "L_ThighRobo03_XT": "LeftUpLeg",
    "L_Leg02_Knee_XB": "LeftLeg",
    "L_KneeRobo01_XT": "LeftLeg",
    "L_KneeRobo02_XT": "LeftLeg",
    "L_KneeRobo03_XT": "LeftLeg",
    "L_KneeRobo04_XT": "LeftLeg",
    "L_Leg03_Ankle_XB": "LeftFoot",
    "L_Leg04_Toes_XL2": "LeftFoot",

    # Right Leg & Foot (Toes merged into RightFoot for solid grounded foot base)
    "R_Leg01_Thigh_XB": "RightUpLeg",
    "R_ThighRobo01_XT": "RightUpLeg",
    "R_ThighRobo02_XT": "RightUpLeg",
    "R_ThighRobo03_XT": "RightUpLeg",
    "R_Leg02_Knee_XB": "RightLeg",
    "R_KneeRobo01_XT": "RightLeg",
    "R_KneeRobo02_XT": "RightLeg",
    "R_KneeRobo03_XT": "RightLeg",
    "R_KneeRobo04_XT": "RightLeg",
    "R_Leg03_Ankle_XB": "RightFoot",
    "R_Leg04_Toes_XL2": "RightFoot",
}

def resolve_target_bone(bone_name):
    if bone_name in BONE_MAPPING:
        return BONE_MAPPING[bone_name]
    bone = demolishor_arm.data.bones.get(bone_name)
    cur = bone
    while cur:
        if cur.name in BONE_MAPPING:
            return BONE_MAPPING[cur.name]
        cur = cur.parent
    return "Hips"

# 7. Collect vertex weights mapped to target 80 bones
print("[*] Remapping vertex groups...")
v_count = len(demolishor_mesh.data.vertices)
new_weights = [{} for _ in range(v_count)]

for vg in demolishor_mesh.vertex_groups:
    src_bone = vg.name
    target_bone = resolve_target_bone(src_bone)
    vg_idx = vg.index
    
    for v in demolishor_mesh.data.vertices:
        for g in v.groups:
            if g.group == vg_idx and g.weight > 0.001:
                w = g.weight
                new_weights[v.index][target_bone] = new_weights[v.index].get(target_bone, 0.0) + w

# 8. Normalize weights & limit to 4 bones per vertex
print("[*] Normalizing & limiting to 4 bones...")
for v_idx in range(v_count):
    w_dict = new_weights[v_idx]
    if not w_dict:
        w_dict["Hips"] = 1.0
        continue
    sorted_w = sorted(w_dict.items(), key=lambda x: x[1], reverse=True)[:4]
    total_w = sum(w for _, w in sorted_w)
    if total_w > 0:
        new_weights[v_idx] = {b: (w / total_w) for b, w in sorted_w}
    else:
        new_weights[v_idx] = {"Hips": 1.0}

# 9. Clear old vertex groups and create new ones for ALL 80 bones
demolishor_mesh.vertex_groups.clear()
for b_name in bone_order:
    demolishor_mesh.vertex_groups.new(name=b_name)

for v_idx in range(v_count):
    for b_name, w in new_weights[v_idx].items():
        vg = demolishor_mesh.vertex_groups[b_name]
        vg.add([v_idx], w, 'REPLACE')

print(f"[✓] Created vertex groups for all 80 bones!")

# Delete Demolishor_ARM
bpy.data.objects.remove(demolishor_arm, do_unlink=True)

# 10. Parent mesh to Armature
demolishor_mesh.parent = arm_obj
mod = demolishor_mesh.modifiers.new(name="Armature", type='ARMATURE')
mod.object = arm_obj
mod.use_vertex_groups = True

demolishor_mesh.name = "cha_demolishor_gs_00"

# 11. Export FBX to Unity Project
out_fbx = Path(r"d:\Agent\tftf\toolchain\unity_build_project\Assets\Demolishor\demolishor_prepared.fbx")
out_fbx.parent.mkdir(parents=True, exist_ok=True)

bpy.ops.export_scene.fbx(
    filepath=str(out_fbx),
    use_selection=False,
    bake_anim=False,
    add_leaf_bones=False,
    apply_scale_options='FBX_SCALE_ALL',
    axis_forward='-Z',
    axis_up='Y'
)

print(f"\n[✓] SUCCESS: Perfectly aligned rigged FBX exported to {out_fbx}!")
