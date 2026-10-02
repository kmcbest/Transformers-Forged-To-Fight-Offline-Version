import json
import bpy
import mathutils
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
FBX_PATH = ROOT / "3rd-party-models" / "transformers-galatic-trials-elita-one" / "source" / "Elita_One.fbx"
REST_JSON = ROOT / "tools" / "elita_one" / "arcee_unity_rest_matrices.json"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_PATH))
arm_fbx = bpy.data.objects.get("SK_CH_11")

print("=== FBX Bones ===")
for bname in ["l_upperarm_skin", "r_upperarm_skin", "l_hand_skin", "r_hand_skin", "head_skin"]:
    b = arm_fbx.data.bones.get(bname)
    print(f"FBX {bname}: Head = {b.head_local}")

with open(REST_JSON, "r") as f:
    rest_data = json.load(f)

C = mathutils.Matrix((
    (1, 0, 0, 0),
    (0, 0, 1, 0),
    (0, 1, 0, 0),
    (0, 0, 0, 1)
))

print("\n=== Arcee Rest Bones (in Blender space C @ M @ C) ===")
for b in rest_data["bones"]:
    if b["name"] in ["LeftArm", "RightArm", "LeftHand", "RightHand", "Head"]:
        m_raw = b["m"]
        M_u = mathutils.Matrix((m_raw[0:4], m_raw[4:8], m_raw[8:12], m_raw[12:16]))
        M_b = C @ M_u @ C
        print(f"Arcee {b['name']}: Translation = {M_b.translation}")
