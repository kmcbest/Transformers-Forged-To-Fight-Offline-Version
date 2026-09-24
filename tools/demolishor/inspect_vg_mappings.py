# -*- coding: utf-8 -*-
import bpy
import sys

sys.stdout.reconfigure(encoding='utf-8')

bpy.ops.wm.read_factory_settings(use_empty=True)
fbx_path = r"d:\Agent\tftf\3rd-party-models\transformers-fall-of-cybertron-demolishor\source\transformers fall of cybertron Demolishor.fbx"
bpy.ops.import_scene.fbx(filepath=fbx_path)

demo_arm = bpy.data.objects.get("Demolishor_ARM")
demo_mesh = bpy.data.objects.get("RB_DemolishorWeaponArm_SKEL.mo.dmx")

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

def resolve(vg_name):
    if vg_name in BONE_MAPPING:
        return BONE_MAPPING[vg_name], "Direct"
    b = demo_arm.data.bones.get(vg_name)
    cur = b
    while cur:
        if cur.name in BONE_MAPPING:
            return BONE_MAPPING[cur.name], f"Parent({cur.name})"
        cur = cur.parent
    return "Hips", "FALLBACK_HIPS"

print(f"{'Vertex Group':30s} -> {'Target Bone':15s} {'Method'}")
print("-" * 65)
fallbacks = []
for vg in sorted(demo_mesh.vertex_groups, key=lambda x: x.name):
    target, method = resolve(vg.name)
    if "FALLBACK" in method:
        fallbacks.append(vg.name)
        print(f"** {vg.name:27s} -> {target:15s} {method}")
    else:
        print(f"   {vg.name:27s} -> {target:15s} {method}")

print(f"\nTotal fallbacks to Hips: {len(fallbacks)}")
