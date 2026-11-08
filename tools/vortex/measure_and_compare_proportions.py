import json
import math
from pathlib import Path
import bpy
import mathutils

ROBOT_BLEND = Path(r"E:\Agent\TFTF-blender\3rd-party-models\vortex\robot\vortex_robot.blend")
BINDPOSE_JSON = Path(r"E:\Agent\TFTF-blender\tools\vortex\grindor_78_authoritative_bindposes.json")

bpy.ops.wm.open_mainfile(filepath=str(ROBOT_BLEND))

with open(BINDPOSE_JSON, "r", encoding="utf-8") as f:
    grindor_data = json.load(f)

# Grindor Blender positions
g_b_pos = {}
for bname, info in grindor_data.items():
    p = info["world_pos"]
    g_b_pos[bname] = mathutils.Vector((p["x"], p["z"], p["y"]))

# Grindor key lengths
g_spine_len = (g_b_pos["Head"] - g_b_pos["Hips"]).length
g_leg_len = (g_b_pos["LeftFoot"] - g_b_pos["LeftUpLeg"]).length
g_arm_len = (g_b_pos["LeftHand"] - g_b_pos["LeftArm"]).length
g_foot_span = (g_b_pos["RightFoot"] - g_b_pos["LeftFoot"]).length
g_hand_span = (g_b_pos["RightHand"] - g_b_pos["LeftHand"]).length

print("--- Grindor Dimensions (Blender World) ---")
print(f"  Head Z: {g_b_pos['Head'].z:.2f}, Hips Z: {g_b_pos['Hips'].z:.2f}, Foot Z: {g_b_pos['LeftFoot'].z:.2f}")
print(f"  Spine length (Hips->Head): {g_spine_len:.2f}")
print(f"  Leg length (UpLeg->Foot): {g_leg_len:.2f}")
print(f"  Arm length (Arm->Hand): {g_arm_len:.2f}")
print(f"  Foot span: {g_foot_span:.2f}")
print(f"  Hand span: {g_hand_span:.2f}")

arm = bpy.data.objects["Vortex_ARM"]
# In raw FOC:
b_head = arm.data.bones.get("bip_head")
b_pelvis = arm.data.bones.get("bip_pelvis")
b_larm = arm.data.bones.get("bip_upperArm_L")
b_lhand = arm.data.bones.get("bip_hand_L")
b_lhip = arm.data.bones.get("bip_hip_L")
b_lfoot = arm.data.bones.get("bip_foot_L")

# In FOC, bones are along local axes. Let's get distance between bone heads in world:
v_spine_len = (b_head.head_local - b_pelvis.head_local).length
v_leg_len = (b_lfoot.head_local - b_lhip.head_local).length
v_arm_len = (b_lhand.head_local - b_larm.head_local).length

print("\n--- Vortex Dimensions (Raw FOC local) ---")
print(f"  Spine length: {v_spine_len:.2f}")
print(f"  Leg length: {v_leg_len:.2f}")
print(f"  Arm length: {v_arm_len:.2f}")

print("\n--- Scale Ratios ---")
print(f"  Spine ratio (Grindor/Vortex): {g_spine_len / v_spine_len:.3f}")
print(f"  Leg ratio (Grindor/Vortex): {g_leg_len / v_leg_len:.3f}")
print(f"  Arm ratio (Grindor/Vortex): {g_arm_len / v_arm_len:.3f}")
avg_scale = (g_spine_len / v_spine_len + g_leg_len / v_leg_len + g_arm_len / v_arm_len) / 3.0
print(f"  Average recommended scale: {avg_scale:.3f}")
