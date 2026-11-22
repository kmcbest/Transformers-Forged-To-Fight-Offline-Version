import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Vortex\vortex_vh_prepared.fbx")

obj = bpy.data.objects.get("cha_vortex_gs_01")
mesh = obj.data
uv_layer = mesh.uv_layers.active

print(f"Total polygons: {len(mesh.polygons)}")
for p_i in range(10):
    p = mesh.polygons[p_i]
    uvs = [uv_layer.data[li].uv for li in p.loop_indices]
    pts = [mesh.vertices[v].co for v in p.vertices]
    print(f"Poly {p_i}: verts={len(p.vertices)}, normal={p.normal}, center={p.center}")
    for vi, u in zip(p.vertices, uvs):
        print(f"   v{vi}: pos={mesh.vertices[vi].co}, uv={u}")
