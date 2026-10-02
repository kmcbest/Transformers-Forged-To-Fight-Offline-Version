import json
import bpy
import mathutils
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
REST_JSON = ROOT / "tools" / "elita_one" / "arcee_unity_rest_matrices.json"
FBX_PATH = ROOT / "3rd-party-models" / "transformers-galatic-trials-elita-one" / "source" / "Elita_One.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_PATH))
arm_fbx = bpy.data.objects.get("SK_CH_11")

with open(REST_JSON, "r") as f:
    rest_data = json.load(f)

C = mathutils.Matrix((
    (1, 0, 0, 0),
    (0, 0, 1, 0),
    (0, 1, 0, 0),
    (0, 0, 0, 1)
))

arcee_bones = {}
for b in rest_data["bones"]:
    m_raw = b["m"]
    M_u = mathutils.Matrix((m_raw[0:4], m_raw[4:8], m_raw[8:12], m_raw[12:16]))
    M_b = C @ M_u @ C
    arcee_bones[b["name"]] = M_b.translation

arc_hand = arcee_bones["LeftHand"]
fbx_hand = arm_fbx.data.bones.get("l_hand_skin").head_local

# Note in FBX: rot_z_90 maps (x, y, z) -> (-y, x, z)
print("Arcee Left Fingers offset from LeftHand:")
for f in ["LeftHandThumb1", "LeftHandIndex1", "LeftHandMiddle1", "LeftHandRing1", "LeftHandPinky1"]:
    offset = arcee_bones[f] - arc_hand
    print(f"  {f:18s}: {offset}")

print("\nElita Left Fingers offset from l_hand_skin (in rotated FBX coords):")
for f in ["l_thumb_01_skin", "l_index_01_skin", "l_middle_01_skin", "l_ring_01_skin", "l_pinky_01_skin"]:
    fb_pos = arm_fbx.data.bones.get(f).head_local
    # rot_z_90
    fb_pos_rot = mathutils.Vector((-fb_pos.y, fb_pos.x, fb_pos.z))
    fbx_hand_rot = mathutils.Vector((-fbx_hand.y, fbx_hand.x, fbx_hand.z))
    offset = (fb_pos_rot - fbx_hand_rot) * (8.840 / 8.083)
    print(f"  {f:18s}: {offset}")
