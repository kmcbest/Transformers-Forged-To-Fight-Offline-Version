import json
import mathutils

REST_JSON = r"E:\Agent\TFTF-blender\tools\elita_one\arcee_unity_rest_matrices.json"
ANIM_JSON = r"E:\Agent\TFTF-blender\tools\elita_one\arcee_attackLight_01.json"
HIERARCHY_JSON = r"E:\Agent\TFTF-blender\tools\elita_one\arcee_bone_hierarchy.json"

with open(REST_JSON, "r") as f:
    rest_data = json.load(f)
u_rest = {b["name"]: b["m"] for b in rest_data["bones"]}

with open(ANIM_JSON, "r") as f:
    anim_data = json.load(f)

with open(HIERARCHY_JSON, "r") as f:
    hierarchy = json.load(f)

f0 = anim_data["frames"][0]
f0_map = {b["name"]: b for b in f0["bones"]}

finger_bones = ["LeftHand", "LeftHandIndex1", "LeftHandIndex2", "LeftHandIndex3"]
for b in finger_bones:
    print(f"Bone: {b}, parent: {hierarchy.get(b)}")
    print(f"  in rest: {b in u_rest}, in anim f0: {b in f0_map}")
    if b in f0_map:
        fb = f0_map[b]
        print(f"  anim pos: ({fb['px']:.3f}, {fb['py']:.3f}, {fb['pz']:.3f}), rot: ({fb['rw']:.3f}, {fb['rx']:.3f}, {fb['ry']:.3f}, {fb['rz']:.3f})")
