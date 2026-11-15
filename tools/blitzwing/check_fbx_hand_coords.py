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

for side in ['Left', 'Right']:
    vgs = [vg.index for vg in mesh.vertex_groups if side in vg.name and ('Hand' in vg.name or 'Finger' in vg.name or 'Thumb' in vg.name)]
    hand_verts = [v.co for v in mesh.data.vertices if any(g.group in vgs and g.weight > 0.05 for g in v.groups)]
    xs = [co.x for co in hand_verts]
    ys = [co.y for co in hand_verts]
    zs = [co.z for co in hand_verts]
    print(f"--- {side} Hand Vertices ({len(hand_verts)} verts) ---")
    print(f"  X: {min(xs):.3f} to {max(xs):.3f}")
    print(f"  Y: {min(ys):.3f} to {max(ys):.3f}")
    print(f"  Z: {min(zs):.3f} to {max(zs):.3f}")
