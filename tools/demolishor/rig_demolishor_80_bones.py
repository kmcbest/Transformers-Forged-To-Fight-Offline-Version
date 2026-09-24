# -*- coding: utf-8 -*-
"""
rig_demolishor_80_bones.py

Builds an Armature in Blender with the exact 80 bones of Ironhide,
loads Demolishor robot mesh, scales it to 10.39m stature,
remaps all vertex groups into the 80 bones, binds to the Armature,
and exports the FBX for Unity.
"""

import sys
import json
import math
from pathlib import Path
import bpy
import mathutils

print("=== Starting Demolishor 80-Bone Rigging in Blender ===")

# Reset Blender
bpy.ops.wm.read_factory_settings(use_empty=True)

# 1. Load the 80 bones data
with open("tools/demolishor/ironhide_80_bones.json", "r", encoding="utf-8") as f:
    bones_data = json.load(f)

bone_order = bones_data["bone_order"]
bones_dict = bones_data["bones"]

# 2. Create the Armature object
arm_data = bpy.data.armatures.new("character_model")
arm_obj = bpy.data.objects.new("character_model", arm_data)
bpy.context.scene.collection.objects.link(arm_obj)
bpy.context.view_layer.objects.active = arm_obj
bpy.ops.object.mode_set(mode='EDIT')

# Create all 80 edit bones
# In Blender, edit_bone needs head and tail.
# We have the 4x4 world matrix for each bone from inverse bindpose.
edit_bones = {}

# Pass 1: create edit bones and set heads
for name in bone_order:
    b_info = bones_dict[name]
    mat = mathutils.Matrix(b_info["matrix"])
    head_pos = mat.to_translation()
    
    eb = arm_data.edit_bones.new(name)
    eb.head = head_pos
    # Temporary tail
    eb.tail = head_pos + mathutils.Vector((0, 0.1, 0))
    edit_bones[name] = eb

# Pass 2: set parents and orient tails
for name in bone_order:
    b_info = bones_dict[name]
    parent_name = b_info.get("parent")
    eb = edit_bones[name]
    if parent_name and parent_name in edit_bones:
        eb.parent = edit_bones[parent_name]
        # Orient parent tail toward child head if not too close
        p_eb = edit_bones[parent_name]
        diff = eb.head - p_eb.head
        if diff.length > 0.05:
            p_eb.tail = eb.head

# Ensure no bone has zero length
for eb in arm_data.edit_bones:
    if (eb.tail - eb.head).length < 0.01:
        eb.tail = eb.head + mathutils.Vector((0, 0.1, 0))

bpy.ops.object.mode_set(mode='OBJECT')
print(f"[✓] Created Armature with {len(arm_obj.data.bones)} bones matching Ironhide SMR!")

# 3. Import Demolishor FBX
fbx_path = r"d:\Agent\tftf\3rd-party-models\transformers-fall-of-cybertron-demolishor\source\transformers fall of cybertron Demolishor.fbx"
bpy.ops.import_scene.fbx(filepath=fbx_path)

demolishor_arm = bpy.data.objects.get("Demolishor_ARM")
demolishor_mesh = bpy.data.objects.get("RB_DemolishorWeaponArm_SKEL.mo.dmx")

# Delete extra objects from import
for obj in list(bpy.data.objects):
    if obj not in [arm_obj, demolishor_mesh, demolishor_arm]:
        bpy.data.objects.remove(obj, do_unlink=True)

# 4. Bone mapping from Demolishor original bones to Ironhide 80 bones
BONE_MAPPING = {
    # Spine & Head
    "C_Root_Reference_XR": "Hips",
    "C_Spine00_Hips_XB": "Hips",
    "C_Spine01_Lumbar01_XB": "Spine",
    "C_Spine02_Lumbar02_XB": "Spine1",
    "C_Head01_Neck_XB": "Neck",
    "C_Head02_Head_XB": "Head",
    "C_Face01_Jaw_XF2": "Jaw",
    # Left Arm
    "L_Arm01_Clav_XB": "LeftShoulder",
    "L_Arm02_Shoulder_XB": "LeftArm",
    "L_Arm03_Elbow_XB": "LeftForeArm",
    "L_Arm04_Hand_XB": "LeftHand",
    "L_Finger01_Thumb01_XL2": "LeftHandThumb1",
    "L_Finger01_Thumb02_XL2": "LeftHandThumb2",
    "L_Finger02_Index01_XL2": "LeftHandIndex1",
    "L_Finger02_Index02_XL2": "LeftHandIndex2",
    "L_Finger03_Middle01_XL2": "LeftHandMiddle1",
    "L_Finger03_Middle02_XL2": "LeftHandMiddle2",
    "L_Finger04_Ring01_XL2": "LeftHandRing1",
    "L_Finger04_Ring02_XL2": "LeftHandRing2",
    "L_Finger05_Pinky01_XL2": "LeftHandPinky1",
    "L_Finger05_Pinky02_XL2": "LeftHandPinky2",
    # Right Arm
    "R_Arm01_Clav_XB": "RightShoulder",
    "R_Arm02_Shoulder_XB": "RightArm",
    "R_Arm03_Elbow_XB": "RightForeArm",
    "R_Arm04_Hand_XB": "RightHand",
    "R_Finger01_Thumb01_XL2": "RightHandThumb1",
    "R_Finger01_Thumb02_XL2": "RightHandThumb2",
    "R_Finger02_Index01_XL2": "RightHandIndex1",
    "R_Finger02_Index02_XL2": "RightHandIndex2",
    "R_Finger03_Middle01_XL2": "RightHandMiddle1",
    "R_Finger03_Middle02_XL2": "RightHandMiddle2",
    "R_Finger04_Ring01_XL2": "RightHandRing1",
    "R_Finger04_Ring02_XL2": "RightHandRing2",
    "R_Finger05_Pinky01_XL2": "RightHandPinky1",
    "R_Finger05_Pinky02_XL2": "RightHandPinky2",
    # Left Leg
    "L_Leg01_Thigh_XB": "LeftUpLeg",
    "L_Leg02_Knee_XB": "LeftLeg",
    "L_Leg03_Ankle_XB": "LeftFoot",
    "L_Leg04_Toes_XL2": "LeftToeBase",
    # Right Leg
    "R_Leg01_Thigh_XB": "RightUpLeg",
    "R_Leg02_Knee_XB": "RightLeg",
    "R_Leg03_Ankle_XB": "RightFoot",
    "R_Leg04_Toes_XL2": "RightToeBase",
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

# 5. Collect vertex weights mapped to target 80 bones
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

# 6. Normalize weights & limit to 4 bones per vertex
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

# 7. Clear old vertex groups and create new ones for ALL 80 bones
demolishor_mesh.vertex_groups.clear()
for b_name in bone_order:
    demolishor_mesh.vertex_groups.new(name=b_name)

# Populate weights
for v_idx in range(v_count):
    for b_name, w in new_weights[v_idx].items():
        vg = demolishor_mesh.vertex_groups[b_name]
        vg.add([v_idx], w, 'REPLACE')

print(f"[✓] Created vertex groups for all 80 bones!")

# Delete Demolishor_ARM
bpy.data.objects.remove(demolishor_arm, do_unlink=True)

# 8. Scale Demolishor Mesh to Ironhide Height (10.42m)
# Original height: ~5.87m. Scale: 1.775
scale_factor = 1.775
print(f"[*] Scaling Demolishor mesh by {scale_factor:.3f}...")
demolishor_mesh.scale = (scale_factor, scale_factor, scale_factor)
bpy.context.view_layer.objects.active = demolishor_mesh
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# 9. Parent mesh to Armature
demolishor_mesh.parent = arm_obj
mod = demolishor_mesh.modifiers.new(name="Armature", type='ARMATURE')
mod.object = arm_obj
mod.use_vertex_groups = True

demolishor_mesh.name = "cha_demolishor_gs_00"

# 10. Export FBX to Unity Project
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

print(f"\n[✓] SUCCESS: Rigged FBX exported with 80 bones to {out_fbx}!")
