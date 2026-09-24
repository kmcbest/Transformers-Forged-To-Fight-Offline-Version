# -*- coding: utf-8 -*-
import bpy
import sys

sys.stdout.reconfigure(encoding='utf-8')

bpy.ops.wm.read_factory_settings(use_empty=True)
fbx_path = r"d:\Agent\tftf\3rd-party-models\transformers-fall-of-cybertron-demolishor\source\transformers fall of cybertron Demolishor.fbx"
bpy.ops.import_scene.fbx(filepath=fbx_path)

mesh = bpy.data.objects.get("RB_DemolishorWeaponArm_SKEL.mo.dmx")
vgs = [vg.name for vg in mesh.vertex_groups]

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

    # Head & Neck & Face
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

    # Left Hand Fingers
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
    "R_Arm04_Hand_XB": "RightHand",

    # Right Hand Fingers
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

    # Left Leg & Foot
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

    # Right Leg & Foot
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

unmapped = [name for name in vgs if name not in BONE_MAPPING]
print(f"Total vertex groups: {len(vgs)}")
print(f"Mapped: {len(vgs) - len(unmapped)} / {len(vgs)}")
if unmapped:
    print("UNMAPPED:", unmapped)
else:
    print("[✓] 100% OF VERTEX GROUPS ARE PERFECTLY MAPPED!")
