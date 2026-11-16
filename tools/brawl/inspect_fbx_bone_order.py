import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Brawl\brawl_robot.fbx")

arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
print(f"Armature: {arm.name}, bones count: {len(arm.data.bones)}")
for idx, b in enumerate(arm.data.bones):
    print(f"[{idx:02d}] {b.name}")
