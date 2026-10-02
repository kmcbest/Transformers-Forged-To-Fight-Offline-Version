import json
import bpy
import math
import mathutils
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
FBX_PATH = ROOT / "3rd-party-models" / "transformers-galatic-trials-elita-one" / "source" / "Elita_One.fbx"
REST_JSON = ROOT / "tools" / "elita_one" / "arcee_unity_rest_matrices.json"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_PATH))

arm_fbx = bpy.data.objects.get("SK_CH_11")
mesh_fbx = bpy.data.objects.get("SK_CH_11.001")

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

scale_s = 8.840 / 8.083
M_transform = mathutils.Matrix.Rotation(math.radians(90.0), 4, 'Z') @ mathutils.Matrix.Scale(scale_s, 4)

# Apply transform to mesh data
mesh_fbx.data.transform(M_transform)
mesh_fbx.data.update()

print(f"Transformed Vert 13000 (l_pinky_03_skin): {mesh_fbx.data.vertices[13000].co}")

# Check key transformed FBX bone heads
print("\nComparing Transformed FBX Bone Heads vs Arcee Bones:")
landmarks = [
    ("Hips", "pelvis_skin", "Hips"),
    ("Spine1 (Chest)", "spine_03_skin", "Spine1"),
    ("Neck", "neck_skin", "Neck"),
    ("Head", "head_skin", "Head"),
    ("L Shoulder", "l_upperarm_skin", "LeftArm"),
    ("R Shoulder", "r_upperarm_skin", "RightArm"),
    ("L Elbow", "l_lowerarm_skin", "LeftForeArm"),
    ("R Elbow", "r_lowerarm_skin", "RightForeArm"),
    ("L Wrist", "l_hand_skin", "LeftHand"),
    ("R Wrist", "r_hand_skin", "RightHand"),
    ("L Hip", "l_upperleg_skin", "LeftUpLeg"),
    ("R Hip", "r_upperleg_skin", "RightUpLeg"),
    ("L Knee", "l_lowerleg_skin", "LeftLeg"),
    ("R Knee", "r_lowerleg_skin", "RightLeg"),
    ("L Ankle", "l_foot_skin", "LeftFoot"),
    ("R Ankle", "r_foot_skin", "RightFoot"),
]

for name, fbx_bname, arc_bname in landmarks:
    fbx_b = arm_fbx.data.bones.get(fbx_bname)
    fbx_pos = M_transform @ fbx_b.head_local
    arc_pos = arcee_bones.get(arc_bname, mathutils.Vector())
    dist = (fbx_pos - arc_pos).length
    print(f"{name:16s} | Transformed FBX: ({fbx_pos.x:6.2f}, {fbx_pos.y:6.2f}, {fbx_pos.z:6.2f}) | Arcee: ({arc_pos.x:6.2f}, {arc_pos.y:6.2f}, {arc_pos.z:6.2f}) | Diff: {dist:5.2f}m")
