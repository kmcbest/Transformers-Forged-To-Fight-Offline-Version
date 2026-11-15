import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from mathutils import Vector, Quaternion, Matrix

fbx_path = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Blitzwing\blitzwing_robot.fbx"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path)

arm_obj = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
mesh_obj = [o for o in bpy.data.objects if o.type == 'MESH'][0]

# Unity (ux, uy, uz, uw) -> Blender rotation
# Let's inspect pose bones in arm_obj
print("Armature pose bones count:", len(arm_obj.pose.bones))
for b in arm_obj.pose.bones:
    if 'thumb' in b.name.lower() or 'index' in b.name.lower():
        print(f"PoseBone: {b.name}")
