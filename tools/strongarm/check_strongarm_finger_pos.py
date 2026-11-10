import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r"E:\Agent\RID_game\strongarm_zip_extracted\source\Strongarm.fbx")

arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
arm.data.pose_position = 'REST'
bpy.context.view_layer.update()

for b in arm.data.bones:
    if 'index' in b.name.lower() or 'thumb' in b.name.lower() or 'wrist' in b.name.lower():
        head = arm.matrix_world @ b.head_local
        tail = arm.matrix_world @ b.tail_local
        print(f"{b.name:25s}: head=({head.x:.3f}, {head.y:.3f}, {head.z:.3f}), tail=({tail.x:.3f}, {tail.y:.3f}, {tail.z:.3f})")
