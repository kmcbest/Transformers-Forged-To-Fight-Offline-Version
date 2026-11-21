import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import bpy
from mathutils import Vector

ROBOT_FBX = r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\01_source\Sideswipe.fbx"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=ROBOT_FBX)

arm = bpy.data.objects.get("Armature")
print(f"Armature matrix_world:\n{arm.matrix_world}")
for bname in ["Bip_Head", "Bip_Spine_1", "Bip_Pelvis", "Bip_Foot_L", "Bip_Foot_R", "Bn_Wheel_L", "Bn_Wheel_R", "Bn_DoorL_1", "Bn_DoorR_1"]:
    b = arm.data.bones.get(bname)
    if b:
        w_head = arm.matrix_world @ b.head_local
        print(f"  Bone {bname:15s} world: ({w_head.x:7.4f}, {w_head.y:7.4f}, {w_head.z:7.4f})")

# Let's check Mesh 20 (chest headlights) in world space
m20 = bpy.data.objects.get("20")
if m20:
    pts = [m20.matrix_world @ v.co for v in m20.data.vertices]
    print(f"Mesh 20 (chest headlights) world pos: ({sum(p.x for p in pts)/len(pts):.4f}, {sum(p.y for p in pts)/len(pts):.4f}, {sum(p.z for p in pts)/len(pts):.4f})")
