import os
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import bpy
import math
from mathutils import Vector, Matrix, Quaternion

ROBOT_FBX = r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\01_source\Sideswipe.fbx"
SUMMARY_PATH = r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\00_donor_reference\donor_summary.json"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=ROBOT_FBX)

import json
import numpy as np

with open(SUMMARY_PATH, "r", encoding="utf-8") as f:
    donor = json.load(f)

mesh_00 = donor["meshes"]["cha_barricade_cin_dotm_00"]
tos_00 = donor["avatars"]["cha_barricade_cin_dotm_00Avatar"]["tos"]

def unity_to_blender(upos):
    return Vector((-float(upos[0]), -float(upos[2]), float(upos[1])))

barr_pos = {}
for idx, (h, bp) in enumerate(zip(mesh_00["boneHashes"], mesh_00["bindposes"])):
    mat = np.array([
        [bp["e00"], bp["e01"], bp["e02"], bp["e03"]],
        [bp["e10"], bp["e11"], bp["e12"], bp["e13"]],
        [bp["e20"], bp["e21"], bp["e22"], bp["e23"]],
        [bp["e30"], bp["e31"], bp["e32"], bp["e33"]]
    ])
    inv_mat = np.linalg.inv(mat)
    bname = tos_00.get(str(h), f"bone_{idx}").split("/")[-1]
    barr_pos[bname] = unity_to_blender(inv_mat[:3, 3])

print("Barricade Arm Positions:")
for bn in ["LeftShoulder", "LeftArm", "LeftForeArm", "LeftHand", "RightShoulder", "RightArm", "RightForeArm", "RightHand"]:
    print(f"  {bn:15s}: {barr_pos[bn]}")

arm = bpy.data.objects.get("Armature")
print(f"Sideswipe Armature found: {arm.name}")
