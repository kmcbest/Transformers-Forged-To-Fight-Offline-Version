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

with open(REST_JSON, "r") as f:
    rest_data = json.load(f)

C = mathutils.Matrix((
    (1, 0, 0, 0),
    (0, 0, 1, 0),
    (0, 1, 0, 0),
    (0, 0, 0, 1)
))

import math
R_rot_z_90 = mathutils.Matrix.Rotation(math.radians(90.0), 4, 'Z')

print("=== FBX Bones vs Arcee Bones Matrix ===")
for fb_name, arc_name in [
    ("head_skin", "Head"),
    ("l_upperarm_skin", "LeftArm"),
    ("l_hand_skin", "LeftHand"),
    ("r_upperarm_skin", "RightArm"),
    ("r_hand_skin", "RightHand"),
    ("r_middle_01_skin", "RightHandMiddle1"),
    ("l_middle_01_skin", "LeftHandMiddle1")
]:
    b_fbx = arm_fbx.data.bones.get(fb_name)
    m_fbx = R_rot_z_90 @ b_fbx.matrix_local
    
    b_arc = [b for b in rest_data["bones"] if b["name"] == arc_name][0]
    m_raw = b_arc["m"]
    M_u = mathutils.Matrix((m_raw[0:4], m_raw[4:8], m_raw[8:12], m_raw[12:16]))
    M_arc = C @ M_u @ C
    
    # Compare their 3x3 rotation matrices
    R_fbx = m_fbx.to_3x3()
    R_arc = M_arc.to_3x3()
    
    # Relative rotation difference
    diff = R_arc.inverted() @ R_fbx
    q_diff = diff.to_quaternion()
    print(f"\nBone {arc_name} (from {fb_name}):")
    print(f"  FBX Head: {m_fbx.translation}")
    print(f"  Arc Head: {M_arc.translation}")
    print(f"  Diff Quat: {q_diff}, Angle: {q_diff.angle * 180 / 3.14159:.1f} deg")
