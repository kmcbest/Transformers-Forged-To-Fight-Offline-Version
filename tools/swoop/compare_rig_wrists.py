import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
from pathlib import Path
import bpy

BP_JSON = Path("e:/Agent/TFTF-blender/tools/swoop/ramjet_78_authoritative_bindposes.json")
with open(BP_JSON, "r", encoding="utf-8") as f:
    data = json.load(f)

# Ramjet bone positions in Blender coords (bx = -ux, by = -uz, bz = uy)
for name in ["LeftForeArm", "LeftHand", "RightForeArm", "RightHand"]:
    ux, uy, uz = data['bones'][name]['unity_world_pos']
    print(f"Ramjet {name}: Blender pos = ({-ux:.3f}, {-uz:.3f}, {uy:.3f})")

# Swoop in raw FBX
FBX_SRC = Path("e:/Agent/TFTF-blender/3rd-party-models/swoop/01_master/Swoop_pbr.fbx")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_SRC))
arm = bpy.data.objects.get("Bip001")
mesh = bpy.data.objects.get("Swoop.001")

vs = [v.co for v in mesh.data.vertices]
min_z, max_z = min(v.z for v in vs), max(v.z for v in vs)
scale_factor = 11.40 / (max_z - min_z)
print(f"Swoop scale_factor: {scale_factor:.4f}")

for bname in ["Bip001 L Forearm", "Bip001 L Hand", "Bone_L_Hand", "Bip001 R Forearm", "Bip001 R Hand", "Bone_R_Hand"]:
    b = arm.data.bones.get(bname)
    if b:
        # bone head in world pos
        whead = arm.matrix_world @ b.head_local
        # apply our scaling & grounding
        scaled_z = (whead.z - min_z) * scale_factor
        scaled_x = whead.x * scale_factor
        scaled_y = whead.y * scale_factor
        print(f"Swoop {bname}: Scaled pos = ({scaled_x:.3f}, {scaled_y:.3f}, {scaled_z:.3f})")
