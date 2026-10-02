import json
import mathutils
from pathlib import Path

ANIM_JSON = Path(r"E:\Agent\TFTF-blender\tools\elita_one\arcee_attackLight_01.json")
REST_JSON = Path(r"E:\Agent\TFTF-blender\tools\elita_one\arcee_unity_rest_matrices.json")

with open(ANIM_JSON, "r") as f:
    anim = json.load(f)
with open(REST_JSON, "r") as f:
    rest = json.load(f)

C = mathutils.Matrix((
    (1, 0, 0, 0),
    (0, 0, 1, 0),
    (0, 1, 0, 0),
    (0, 0, 0, 1)
))

frame0 = {b["name"]: b for b in anim["frames"][0]["bones"]}
rest_map = {b["name"]: b for b in rest["bones"]}

print(f"{'Bone':20s} | {'Rest Pos (Blender)':24s} | {'Anim Pos Frame 0 (Blender)':24s}")
print("-" * 75)
for bname in ["Hips", "Spine1", "LeftArm", "LeftForeArm", "LeftHand", "LeftHandPinky2", "RightArm", "RightForeArm", "RightHand", "RightHandPinky2"]:
    r_m = rest_map[bname]["m"]
    M_u_r = mathutils.Matrix((r_m[0:4], r_m[4:8], r_m[8:12], r_m[12:16]))
    pos_r = (C @ M_u_r @ C).translation
    
    a_m = frame0[bname]["m"]
    M_u_a = mathutils.Matrix((a_m[0:4], a_m[4:8], a_m[8:12], a_m[12:16]))
    pos_a = (C @ M_u_a @ C).translation
    
    print(f"{bname:20s} | ({pos_r.x:6.2f}, {pos_r.y:6.2f}, {pos_r.z:6.2f}) | ({pos_a.x:6.2f}, {pos_a.y:6.2f}, {pos_a.z:6.2f})")
