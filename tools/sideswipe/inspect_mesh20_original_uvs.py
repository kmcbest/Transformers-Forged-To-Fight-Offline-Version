import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

fbx_path = r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\01_source\Sideswipe.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path)

o20 = bpy.data.objects.get("20")
if o20:
    uvl = o20.data.uv_layers.active
    print("Mesh 20 original UVs:")
    for pi, p in enumerate(o20.data.polygons):
        uvs = [uvl.data[li].uv for li in p.loop_indices]
        print(f"  Poly {pi}: verts={list(p.vertices)}, UVs={[(round(u[0], 4), round(u[1], 4)) for u in uvs]}")
