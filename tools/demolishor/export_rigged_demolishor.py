# -*- coding: utf-8 -*-
import bpy
import sys
from pathlib import Path

print("=== Rigging Demolishor with Armature in Blender ===")

bpy.ops.wm.read_factory_settings(use_empty=True)

fbx_path = r"d:\Agent\tftf\3rd-party-models\transformers-fall-of-cybertron-demolishor\source\transformers fall of cybertron Demolishor.fbx"
bpy.ops.import_scene.fbx(filepath=fbx_path)

arm = bpy.data.objects.get("Demolishor_ARM")
mesh = bpy.data.objects.get("RB_DemolishorWeaponArm_SKEL.mo.dmx")

# Delete vehicle and other meshes
for obj in list(bpy.data.objects):
    if obj not in [arm, mesh]:
        bpy.data.objects.remove(obj, do_unlink=True)

BONE_RENAME = {
    # Spine & Head
    "C_Root_Reference_XR": "Reference",
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

# 1. Rename bones in armature
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='EDIT')
renamed_count = 0
for b in arm.data.edit_bones:
    if b.name in BONE_RENAME:
        b.name = BONE_RENAME[b.name]
        renamed_count += 1
bpy.ops.object.mode_set(mode='OBJECT')
print(f"[✓] Renamed {renamed_count} primary bones in Armature!")

# 2. Also rename matching vertex groups in mesh
for vg in mesh.vertex_groups:
    if vg.name in BONE_RENAME:
        vg.name = BONE_RENAME[vg.name]

# 3. Scale both Armature and Mesh by 1.77
scale_factor = 1.77
arm.scale = (scale_factor, scale_factor, scale_factor)
mesh.scale = (scale_factor, scale_factor, scale_factor)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bpy.context.view_layer.objects.active = mesh
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# 4. Limit weights to 4 bones per vertex
bpy.context.view_layer.objects.active = mesh
bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
bpy.ops.object.vertex_group_limit_total(group_select_mode='ALL', limit=4)
bpy.ops.object.vertex_group_normalize_all(group_select_mode='ALL', lock_active=False)
bpy.ops.object.mode_set(mode='OBJECT')
print("[✓] Limited weights to 4 bones and normalized!")

# 5. Rename objects
mesh.name = "cha_demolishor_gs_00"
arm.name = "character_model"

# Export rigged FBX
out_fbx = Path(r"d:\Agent\tftf\toolchain\unity_build_project\Assets\Demolishor\demolishor_prepared.fbx")
bpy.ops.export_scene.fbx(
    filepath=str(out_fbx),
    use_selection=False,
    bake_anim=False,
    add_leaf_bones=False
)
print(f"[✓] Successfully exported rigged FBX to {out_fbx}!")
