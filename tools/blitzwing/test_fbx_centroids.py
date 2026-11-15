import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from mathutils import Vector

bpy.ops.wm.read_factory_settings(use_empty=True)
fbx_path = r'E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Blitzwing\blitzwing_robot.fbx'
bpy.ops.import_scene.fbx(filepath=fbx_path)

mesh = [o for o in bpy.context.scene.objects if o.type == 'MESH'][0]

for bname in ['LeftHand', 'RightHand', 'LeftFoot', 'LeftToeBase']:
    vgs = [vg.index for vg in mesh.vertex_groups if vg.name == bname]
    if vgs:
        vs = [v.co for v in mesh.data.vertices if any(g.group == vgs[0] and g.weight > 0.3 for g in v.groups)]
        if vs:
            c = sum(vs, Vector()) / len(vs)
            print(f"{bname:12s} centroid: {c} (count={len(vs)})")
