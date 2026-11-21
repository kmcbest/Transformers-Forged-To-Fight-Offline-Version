import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path

source_fbx = Path(r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\01_source\Sideswipe.fbx")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(source_fbx))

mesh_20 = bpy.data.objects.get("20")
if mesh_20:
    print(f"Mesh 20 found: verts={len(mesh_20.data.vertices)}, polys={len(mesh_20.data.polygons)}")
    mats = [m.name for m in mesh_20.data.materials if m]
    print(f"Materials on Mesh 20: {mats}")
    xs = [v.co.x for v in mesh_20.data.vertices]
    ys = [v.co.y for v in mesh_20.data.vertices]
    zs = [v.co.z for v in mesh_20.data.vertices]
    print(f"Mesh 20 3D bounds: X=[{min(xs):.2f}, {max(xs):.2f}], Y=[{min(ys):.2f}, {max(ys):.2f}], Z=[{min(zs):.2f}, {max(zs):.2f}]")
    uvl = mesh_20.data.uv_layers.active
    if uvl:
        uvs = [uvl.data[li].uv for p in mesh_20.data.polygons for li in p.loop_indices]
        us = [uv[0] for uv in uvs]
        vs = [uv[1] for uv in uvs]
        print(f"Original UV bounds: U=[{min(us):.3f}, {max(us):.3f}], V=[{min(vs):.3f}, {max(vs):.3f}]")
else:
    print("Mesh 20 not found in FBX")
