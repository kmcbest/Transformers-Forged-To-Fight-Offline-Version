import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
import zipfile
import tempfile
import os

bpy.ops.wm.read_factory_settings(use_empty=True)
with zipfile.ZipFile(r"O:\agent\transformers-fall-of-cybertron-combaticons.zip", "r") as z:
    tmp_dir = tempfile.mkdtemp()
    fbx_name = "source/transformers fall of cybertron convaticons .fbx"
    z.extract(fbx_name, tmp_dir)
    bpy.ops.import_scene.fbx(filepath=os.path.join(tmp_dir, fbx_name))

o = bpy.data.objects.get("VH_Vortex_SKEL.001.dmx")
m = o.data
print("=== Source VH_Vortex_SKEL.001.dmx ===")
print("Materials:", [(i, mat.name if mat else None) for i, mat in enumerate(m.materials)])
for mi, mat in enumerate(m.materials):
    cnt = sum(1 for p in m.polygons if p.material_index == mi)
    print(f"  Mat[{mi}] '{mat.name}': {cnt} polys")
    if mat and mat.use_nodes:
        for node in mat.node_tree.nodes:
            if node.type == "TEX_IMAGE" and node.image:
                print(f"    Image node: {node.image.name} -> {node.image.filepath}")

print("UV layers:", [u.name for u in m.uv_layers])
for uvi, uv_l in enumerate(m.uv_layers):
    sample_uvs = [uv_l.data[i].uv[:] for i in range(0, min(20, len(uv_l.data)), 3)]
    print(f"  UV[{uvi}] '{uv_l.name}' samples: {[(round(x[0],3), round(x[1],3)) for x in sample_uvs]}")

# Now inspect vortex_vh_prepared.fbx
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Vortex\vortex_vh_prepared.fbx")
po = bpy.data.objects.get("cha_vortex_gs_01")
pm = po.data
print("\n=== Prepared vortex_vh_prepared.fbx ===")
print("Materials:", [mat.name if mat else None for mat in pm.materials])
print("UV layers:", [u.name for u in pm.uv_layers])
for uvi, uv_l in enumerate(pm.uv_layers):
    sample_uvs = [uv_l.data[i].uv[:] for i in range(0, min(20, len(uv_l.data)), 3)]
    print(f"  UV[{uvi}] '{uv_l.name}' samples: {[(round(x[0],3), round(x[1],3)) for x in sample_uvs]}")
