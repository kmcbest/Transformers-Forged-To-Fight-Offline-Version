import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)

fbx_path = r'E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Blitzwing\blitzwing_robot.fbx'
bpy.ops.import_scene.fbx(filepath=fbx_path)

mesh = [o for o in bpy.context.scene.objects if o.type == 'MESH'][0]
print(f"Loaded FBX mesh: {mesh.name}, total verts: {len(mesh.data.vertices)}")

all_vgs = [vg.name for vg in mesh.vertex_groups]
print(f"Total vertex groups: {len(all_vgs)}")
for i, name in enumerate(all_vgs):
    print(f"  [{i:02d}] {name}")
