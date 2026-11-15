import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
fbx_path = r'E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Blitzwing\blitzwing_robot.fbx'
bpy.ops.import_scene.fbx(filepath=fbx_path)

arm = [o for o in bpy.context.scene.objects if o.type == 'ARMATURE'][0]
for bname in ['Head', 'Hips', 'LeftUpLeg', 'LeftLeg', 'LeftFoot', 'LeftToeBase', 'LeftArm', 'LeftForeArm', 'LeftHand']:
    b = arm.data.bones.get(bname)
    if b:
        print(f"  {bname:14s}: head={b.head} | matrix_local.translation={b.matrix_local.translation}")
