import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path

# Open Strongarm.fbx before joining, and let's check what each submesh's vertex groups are
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r"E:\Agent\RID_game\strongarm_zip_extracted\source\Strongarm.fbx")

# Mapping from build_aligned_strongarm.py
vg_to_prowl = {
    "bot:jt_pelvis": "Hips",
    "bot:jt_spine1": "Spine",
    "bot:jt_spine2": "Spine1",
    "bot:jt_spine3": "Spine1",
    "bot:jt_neck": "Head",
    "bot:jt_head": "Head",
    "bot:jt_face": "Head",
    "bot:jt_clav_L": "LeftShoulder",
    "bot:jt_shoulder_L": "LeftArm",
    "bot:jt_armTip_L": "LeftForeArm",
    "bot:jt_elbow_L": "LeftForeArm",
    "bot:jt_wrist_L": "LeftHand",
    "bot:jt_hand_L": "LeftHand",
    "bot:jt_clav_R": "RightShoulder",
    "bot:jt_shoulder_R": "RightArm",
    "bot:jt_armTip_R": "RightForeArm",
    "bot:jt_elbow_R": "RightForeArm",
    "bot:jt_wrist_R": "RightHand",
    "bot:jt_hand_R": "RightHand",
    "bot:jt_hip_L": "LeftUpLeg",
    "bot:jt_hipArmor_L": "LeftUpLeg",
    "bot:jt_knee_L": "LeftLeg",
    "bot:jt_ankleArmor1_L": "LeftLeg",
    "bot:jt_ankleArmor2_L": "LeftLeg",
    "bot:jt_ankleArmor4_L": "LeftLeg",
    "bot:jt_ankle_L": "LeftToeBase",
    "bot:jt_toe_L": "LeftToeBase",
    "bot:jt_hip_R": "RightUpLeg",
    "bot:jt_hipArmor_R": "RightUpLeg",
    "bot:jt_knee_R": "RightLeg",
    "bot:jt_ankleArmor1_R": "RightLeg",
    "bot:jt_ankleArmor2_R": "RightLeg",
    "bot:jt_ankleArmor4_R": "RightLeg",
    "bot:jt_ankle_R": "RightToeBase",
    "bot:jt_toe_R": "RightToeBase",
    "bot:jt_wing_L": "LeftShoulder",
    "bot:jt_wing_R": "RightShoulder",
    # Fingers
    "bot:jt_thumb1_L": "LeftHandThumb1",
    "bot:jt_thumb2_L": "LeftHandThumb2",
    "bot:jt_thumb3_L": "LeftHandThumb3",
    "bot:jt_index1_L": "LeftHandIndex1",
    "bot:jt_index2_L": "LeftHandIndex2",
    "bot:jt_index3_L": "LeftHandIndex3",
    "bot:jt_middle1_L": "LeftHandMiddle1",
    "bot:jt_middle2_L": "LeftHandMiddle2",
    "bot:jt_middle3_L": "LeftHandMiddle3",
    "bot:jt_ring1_L": "LeftHandRing1",
    "bot:jt_ring2_L": "LeftHandRing2",
    "bot:jt_ring3_L": "LeftHandRing3",
    "bot:jt_pinky1_L": "LeftHandPinky1",
    "bot:jt_pinky2_L": "LeftHandPinky2",
    "bot:jt_pinky3_L": "LeftHandPinky3",
    "bot:jt_thumb1_R": "RightHandThumb1",
    "bot:jt_thumb2_R": "RightHandThumb2",
    "bot:jt_thumb3_R": "RightHandThumb3",
    "bot:jt_index1_R": "RightHandIndex1",
    "bot:jt_index2_R": "RightHandIndex2",
    "bot:jt_index3_R": "RightHandIndex3",
    "bot:jt_middle1_R": "RightHandMiddle1",
    "bot:jt_middle2_R": "RightHandMiddle2",
    "bot:jt_middle3_R": "RightHandMiddle3",
    "bot:jt_ring1_R": "RightHandRing1",
    "bot:jt_ring2_R": "RightHandRing2",
    "bot:jt_ring3_R": "RightHandRing3",
    "bot:jt_pinky1_R": "RightHandPinky1",
    "bot:jt_pinky2_R": "RightHandPinky2",
    "bot:jt_pinky3_R": "RightHandPinky3",
}

print("Checking submeshes for unmapped vertex groups or unassigned vertices:")
total_unassigned = 0
for o in bpy.data.objects:
    if o.type == 'MESH':
        if o.name in ["bot:mask_geo", "bot:faceMaskOn_jaw_geo"]:
            continue
        mapped_vgs = [vg for vg in o.vertex_groups if vg.name in vg_to_prowl]
        unmapped_vgs = [vg.name for vg in o.vertex_groups if vg.name not in vg_to_prowl]
        if unmapped_vgs:
            print(f"Submesh {o.name}: UNMAPPED VGs: {unmapped_vgs}")
        
        # Check how many vertices have weight in mapped groups
        mapped_indices = {vg.index for vg in mapped_vgs}
        unassigned = 0
        for v in o.data.vertices:
            if not any(g.group in mapped_indices and g.weight > 0.001 for g in v.groups):
                unassigned += 1
        if unassigned > 0:
            print(f"Submesh {o.name}: {unassigned}/{len(o.data.vertices)} UNASSIGNED vertices!")
            total_unassigned += unassigned

print(f"\nTotal unassigned vertices across all kept submeshes: {total_unassigned}")
