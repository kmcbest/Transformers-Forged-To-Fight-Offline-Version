import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
import json
import math
from pathlib import Path

ROBOT_BLEND = Path(r"E:\Agent\TFTF-blender\3rd-party-models\vortex\robot\vortex_robot.blend")
BINDPOSE_JSON = Path(r"E:\Agent\TFTF-blender\tools\vortex\grindor_78_authoritative_bindposes.json")

bpy.ops.wm.open_mainfile(filepath=str(ROBOT_BLEND))

with open(BINDPOSE_JSON, "r", encoding="utf-8") as f:
    grindor_data = json.load(f)

# Scale and rotate Vortex_ARM
arm = bpy.data.objects.get("Vortex_ARM")
scale_factor = 2.24
arm.scale = (scale_factor, scale_factor, scale_factor)
arm.rotation_euler = (0, 0, math.radians(-90)) # Face -Y
bpy.context.view_layer.update()

print("--- Comparing Vortex Joints with Grindor Bindposes ---")
# Key bones map: Vortex FOC bone -> Grindor bone
bone_map = {
    "bip_head": "Head",
    "bip_neck": "Neck",
    "bip_spine_1": "Spine1",
    "bip_spine_0": "Spine",
    "bip_pelvis": "Hips",
    "bip_upperArm_L": "LeftArm",
    "bip_lowerArm_L": "LeftForeArm",
    "bip_hand_L": "LeftHand",
    "bip_upperArm_R": "RightArm",
    "bip_lowerArm_R": "RightForeArm",
    "bip_hand_R": "RightHand",
    "bip_hip_L": "LeftUpLeg",
    "bip_knee_L": "LeftLeg",
    "bip_foot_L": "LeftFoot",
    "bip_hip_R": "RightUpLeg",
    "bip_knee_R": "RightLeg",
    "bip_foot_R": "RightFoot"
}

for v_bname, g_bname in bone_map.items():
    vb = arm.data.bones.get(v_bname)
    g_info = grindor_data.get(g_bname)
    if vb and g_info:
        # world position of Vortex bone head
        v_world = arm.matrix_world @ vb.head
        g_pos = g_info["world_pos"]
        # In Unity: X is right (+X), Y is up (+Y), Z is forward (+Z)
        # In Blender: X is right (+X), Y is forward (-Y), Z is up (+Z)
        # So Unity (X, Y, Z) corresponds to Blender (X, -Z, Y) or similar.
        print(f"Vortex {v_bname:16s} world: ({v_world.x:6.2f}, {v_world.y:6.2f}, {v_world.z:6.2f}) | Grindor {g_bname:14s} unity: ({g_pos['x']:6.2f}, {g_pos['y']:6.2f}, {g_pos['z']:6.2f})")
