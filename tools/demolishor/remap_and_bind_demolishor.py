# -*- coding: utf-8 -*-
import bpy
import json
import mathutils
from pathlib import Path

print("=== Starting Demolishor Remap & Rigging in Blender ===")

# Reset Blender
bpy.ops.wm.read_factory_settings(use_empty=True)

# 1. Load Demolishor FBX
fbx_path = r"d:\Agent\tftf\3rd-party-models\transformers-fall-of-cybertron-demolishor\source\transformers fall of cybertron Demolishor.fbx"
bpy.ops.import_scene.fbx(filepath=fbx_path)

demolishor_arm = bpy.data.objects.get("Demolishor_ARM")
demolishor_mesh = bpy.data.objects.get("RB_DemolishorWeaponArm_SKEL.mo.dmx")

# Remove unused vehicle and collision objects
for obj in list(bpy.data.objects):
    if obj not in [demolishor_arm, demolishor_mesh]:
        bpy.data.objects.remove(obj, do_unlink=True)

# 2. Build bone ancestor lookup for Demolishor
BONE_MAPPING = {
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

# 3. Collect vertex weights mapped to target bones
print("[*] Remapping vertex groups...")
v_count = len(demolishor_mesh.data.vertices)
# vertex_weights: list of dict {target_bone_name: weight}
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

# 4. Limit to 4 bones and normalize weights
print("[*] Normalizing & limiting to 4 bones...")
for v_idx in range(v_count):
    w_dict = new_weights[v_idx]
    if not w_dict:
        w_dict["Hips"] = 1.0
        continue
    # Sort by weight descending, keep top 4
    sorted_w = sorted(w_dict.items(), key=lambda x: x[1], reverse=True)[:4]
    total_w = sum(w for _, w in sorted_w)
    if total_w > 0:
        new_weights[v_idx] = {b: (w / total_w) for b, w in sorted_w}
    else:
        new_weights[v_idx] = {"Hips": 1.0}

# 5. Clear old vertex groups and create new ones
demolishor_mesh.vertex_groups.clear()
target_vgs = {}

for v_idx in range(v_count):
    for b_name, w in new_weights[v_idx].items():
        if b_name not in target_vgs:
            target_vgs[b_name] = demolishor_mesh.vertex_groups.new(name=b_name)
        target_vgs[b_name].add([v_idx], w, 'REPLACE')

print(f"[✓] Created {len(target_vgs)} new vertex groups mapped to Ironhide skeleton!")

# 6. Scale and Align Demolishor Mesh to Ironhide Dimensions
# Ironhide Height: ~10.42. Demolishor Height: ~5.87.
# Scale factor: 10.42 / 5.87 = ~1.775
scale_factor = 1.77
print(f"[*] Scaling Demolishor mesh by {scale_factor:.2f} to match Ironhide stature...")
demolishor_mesh.scale = (scale_factor, scale_factor, scale_factor)
bpy.context.view_layer.objects.active = demolishor_mesh
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# 7. Rename mesh and assign Armature modifier
demolishor_mesh.name = "cha_demolishor_gs_00"

# Remove Demolishor_ARM
bpy.data.objects.remove(demolishor_arm, do_unlink=True)

# Export intermediate FBX
out_fbx = Path(r"d:\Agent\tftf\tools\demolishor\demolishor_prepared.fbx")
bpy.ops.export_scene.fbx(
    filepath=str(out_fbx),
    use_selection=False,
    bake_anim=False
)
print(f"[✓] Successfully exported prepared mesh to {out_fbx}")
