import bpy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
BLEND_FILE = ROOT / "tools" / "elita_one" / "elita_one_arcee_setup.blend"

bpy.ops.wm.open_mainfile(filepath=str(BLEND_FILE))
elita_mesh = bpy.data.objects.get("Elita_One_Mesh")

vg_names = [vg.name for vg in elita_mesh.vertex_groups]
print(f"Elita One has {len(vg_names)} vertex groups:")

# Explicit Anatomy-Constrained Mapping
ELITA_TO_ARCEE = {
    # Pelvis & Torso
    "root": "Hips",
    "cog": "Hips",
    "pelvis_skin": "Hips",
    "l_cover_hips_skin": "Hips",
    "r_cover_hips_skin": "Hips",
    "spine_01_skin": "Spine",
    "spine_02_skin": "Spine1",
    "spine_03_skin": "Spine1",
    "cover_chest_skin": "Spine1",
    "cover_chest_skin_end": "Spine1",
    "cover_body_back_skin": "Spine1",
    "l_upper_cover_wheel_skin": "Spine1",
    "l_upper_wheel_skin": "Spine1",
    "l_upper_wheel_skin_end": "Spine1",
    "r_upper_cover_wheel_skin": "Spine1",
    "r_upper_wheel_skin": "Spine1",
    "r_upper_wheel_skin_end": "Spine1",
    
    # Neck & Head
    "neck_skin": "Neck",
    "head_skin": "Head",
    "head_skin_end": "Head",
    
    # Left Arm
    "l_clavicle_skin": "LeftShoulder",
    "l_shoulder_pistons_skin": "LeftShoulderPad",
    "l_shoulder_pistons_skin_end": "LeftShoulderPad",
    "l_upperarm_skin": "LeftArm",
    "l_cover_upper_arm_skin": "LeftArm",
    "l_cover_upper_arm_skin_end": "LeftArm",
    "l_upper_arm_part_01_skin": "LeftArmRoll",
    "l_upper_arm_part_02_skin": "LeftArmRoll",
    "l_upper_arm_part_02_skin_end": "LeftArmRoll",
    "l_lowerarm_skin": "LeftForeArm",
    "l_cover_lower_arm_skin": "LeftForeArm",
    "l_piston_lower_arm_end_skin": "LeftForeArm",
    "l_piston_lower_arm_end_skin_end": "LeftForeArm",
    "l_piston_lower_arm_start_skin": "LeftForeArmRoll",
    "l_piston_lower_arm_start_skin_end": "LeftForeArmRoll",
    "l_lower_cover_wheel_skin": "LeftForeArm",
    "l_lower_wheel_skin": "LeftForeArm",
    "l_lower_wheel_skin_end": "LeftForeArm",
    "l_hand_skin": "LeftHand",
    "SOCKET_weapon": "LeftProp",
    "SOCKET_weapon_end": "LeftProp",
    
    # Left Fingers (Exact 1:1)
    "l_thumb_01_skin": "LeftHandThumb1",
    "l_thumb_02_skin": "LeftHandThumb2",
    "l_thumb_03_skin": "LeftHandThumb3",
    "l_thumb_03_skin_end": "LeftHandThumb3",
    "l_index_01_skin": "LeftHandIndex1",
    "l_index_02_skin": "LeftHandIndex2",
    "l_index_03_skin": "LeftHandIndex3",
    "l_index_03_skin_end": "LeftHandIndex3",
    "l_middle_01_skin": "LeftHandMiddle1",
    "l_middle_02_skin": "LeftHandMiddle2",
    "l_middle_03_skin": "LeftHandMiddle3",
    "l_middle_03_skin_end": "LeftHandMiddle3",
    "l_ring_01_skin": "LeftHandRing1",
    "l_ring_02_skin": "LeftHandRing2",
    "l_ring_03_skin": "LeftHandRing3",
    "l_ring_03_skin_end": "LeftHandRing3",
    "l_pinky_01_skin": "LeftHandPinky1",
    "l_pinky_02_skin": "LeftHandPinky2",
    "l_pinky_03_skin": "LeftHandPinky3",
    "l_pinky_03_skin_end": "LeftHandPinky3",
    
    # Right Arm
    "r_clavicle_skin": "RightShoulder",
    "r_shoulder_pistons_skin": "RightShoulderPad",
    "r_shoulder_pistons_skin_end": "RightShoulderPad",
    "r_upperarm_skin": "RightArm",
    "r_cover_upper_arm_skin": "RightArm",
    "r_cover_upper_arm_skin_end": "RightArm",
    "r_upper_arm_part_01_skin": "RightArmRoll",
    "r_upper_arm_part_02_skin": "RightArmRoll",
    "r_upper_arm_part_02_skin_end": "RightArmRoll",
    "r_lowerarm_skin": "RightForeArm",
    "r_cover_lower_arm_skin": "RightForeArm",
    "r_piston_lower_arm_end_skin": "RightForeArm",
    "r_piston_lower_arm_end_skin_end": "RightForeArm",
    "r_piston_lower_arm_start_skin": "RightForeArmRoll",
    "r_piston_lower_arm_start_skin_end": "RightForeArmRoll",
    "r_lower_cover_wheel_skin": "RightForeArm",
    "r_lower_wheel_skin": "RightForeArm",
    "r_lower_wheel_skin_end": "RightForeArm",
    "r_hand_skin": "RightHand",
    "SOCKET_skill": "RightProp",
    "SOCKET_skill_end": "RightProp",
    
    # Right Fingers (Exact 1:1)
    "r_thumb_01_skin": "RightHandThumb1",
    "r_thumb_02_skin": "RightHandThumb2",
    "r_thumb_03_skin": "RightHandThumb3",
    "r_thumb_03_skin_end": "RightHandThumb3",
    "r_index_01_skin": "RightHandIndex1",
    "r_index_02_skin": "RightHandIndex2",
    "r_index_03_skin": "RightHandIndex3",
    "r_index_03_skin_end": "RightHandIndex3",
    "r_middle_01_skin": "RightHandMiddle1",
    "r_middle_02_skin": "RightHandMiddle2",
    "r_middle_03_skin": "RightHandMiddle3",
    "r_middle_03_skin_end": "RightHandMiddle3",
    "r_ring_01_skin": "RightHandRing1",
    "r_ring_02_skin": "RightHandRing2",
    "r_ring_03_skin": "RightHandRing3",
    "r_ring_03_skin_end": "RightHandRing3",
    "r_pinky_01_skin": "RightHandPinky1",
    "r_pinky_02_skin": "RightHandPinky2",
    "r_pinky_03_skin": "RightHandPinky3",
    "r_pinky_03_skin_end": "RightHandPinky3",
    
    # Left Leg
    "l_upperleg_skin": "LeftUpLeg",
    "l_piston_leg_end_01_skin": "LeftUpLeg",
    "l_piston_leg_end_01_skin_end": "LeftUpLeg",
    "l_piston_leg_end_02_skin": "LeftUpLeg",
    "l_piston_leg_end_02_skin_end": "LeftUpLeg",
    "l_lowerleg_skin": "LeftLeg",
    "l_piston_leg_start_01_skin": "LeftLeg",
    "l_piston_leg_start_01_skin_end": "LeftLeg",
    "l_piston_leg_start_02_skin": "LeftLeg",
    "l_piston_leg_start_02_skin_end": "LeftLeg",
    "l_piston_leg_end_01_skin1": "LeftLeg",
    "l_piston_leg_end_01_skin1_end": "LeftLeg",
    "l_piston_leg_end_02_skin2": "LeftLeg",
    "l_piston_leg_end_02_skin2_end": "LeftLeg",
    "l_piston_leg_start_01_skin3": "LeftLeg",
    "l_piston_leg_start_01_skin3_end": "LeftLeg",
    "l_piston_leg_start_02_skin4": "LeftLeg",
    "l_piston_leg_start_02_skin4_end": "LeftLeg",
    "l_foot_skin": "LeftFoot",
    "l_foot_heel_skin": "Left_FootFx",
    "l_foot_heel_skin_end": "Left_FootFx",
    "l_foot_toes_skin": "LeftToeBase",
    "l_foot_toes_skin_end": "LeftToe",
    
    # Right Leg
    "r_upperleg_skin": "RightUpLeg",
    "r_piston_leg_end_01_skin": "RightUpLeg",
    "r_piston_leg_end_01_skin_end": "RightUpLeg",
    "r_piston_leg_end_02_skin": "RightUpLeg",
    "r_piston_leg_end_02_skin_end": "RightUpLeg",
    "r_lowerleg_skin": "RightLeg",
    "r_piston_leg_start_01_skin": "RightLeg",
    "r_piston_leg_start_01_skin_end": "RightLeg",
    "r_piston_leg_start_02_skin": "RightLeg",
    "r_piston_leg_start_02_skin_end": "RightLeg",
    "r_piston_leg_end_01_skin5": "RightLeg",
    "r_piston_leg_end_01_skin5_end": "RightLeg",
    "r_piston_leg_end_02_skin6": "RightLeg",
    "r_piston_leg_end_02_skin6_end": "RightLeg",
    "r_piston_leg_start_01_skin7": "RightLeg",
    "r_piston_leg_start_01_skin7_end": "RightLeg",
    "r_piston_leg_start_02_skin8": "RightLeg",
    "r_piston_leg_start_02_skin8_end": "RightLeg",
    "r_foot_skin": "RightFoot",
    "r_foot_heel_skin": "Right_FootFx",
    "r_foot_heel_skin_end": "Right_FootFx",
    "r_foot_toes_skin": "RightToeBase",
    "r_foot_toes_skin_end": "RightToe",
}

print(f"\nTotal mappings defined: {len(ELITA_TO_ARCEE)}")
unmapped = [vg for vg in vg_names if vg not in ELITA_TO_ARCEE]
print(f"Unmapped vertex groups: {len(unmapped)}")
if unmapped:
    for u in unmapped:
        print("  UNMAPPED:", u)
else:
    print("[✓] ALL 94 vertex groups are 100% covered!")

OUT_JSON = ROOT / "tools" / "elita_one" / "elita_to_arcee_mapping.json"
OUT_JSON.write_text(json.dumps(ELITA_TO_ARCEE, indent=2), encoding="utf-8")
print(f"[✓] Saved mapping table to: {OUT_JSON}")
