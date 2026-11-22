import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
import zipfile
import tempfile
import os

with zipfile.ZipFile(r"O:\agent\transformers-fall-of-cybertron-combaticons.zip", "r") as z:
    for n in ["textures/vh_interior_mat.jpg", "textures/vh_interior_n.jpg", "textures/vh.jpg"]:
        if n in z.namelist():
            out_p = rf"e:\Agent\TFTF-blender\tools\vortex\diag\orig_{os.path.basename(n)}"
            with open(out_p, "wb") as f:
                f.write(z.read(n))
            print(f"Extracted {n} -> {out_p}")

    bpy.ops.wm.read_factory_settings(use_empty=True)
    tmp_dir = tempfile.mkdtemp()
    fbx_name = "source/transformers fall of cybertron convaticons .fbx"
    z.extract(fbx_name, tmp_dir)
    bpy.ops.import_scene.fbx(filepath=os.path.join(tmp_dir, fbx_name))

o = bpy.data.objects.get("VH_Vortex_SKEL.001.dmx")
m = o.data
mat2_polys = [p for p in m.polygons if p.material_index == 2]
print(f"\nMat[2] 'TR_Test_Mat_INST' polygon count: {len(mat2_polys)}")
xs = [m.vertices[v].co.x for p in mat2_polys for v in p.vertices]
ys = [m.vertices[v].co.y for p in mat2_polys for v in p.vertices]
zs = [m.vertices[v].co.z for p in mat2_polys for v in p.vertices]
print(f"Mat[2] bbox: X=[{min(xs):.2f}..{max(xs):.2f}], Y=[{min(ys):.2f}..{max(ys):.2f}], Z=[{min(zs):.2f}..{max(zs):.2f}]")

uv_l = m.uv_layers.active
us = [uv_l.data[li].uv.x for p in mat2_polys for li in p.loop_indices]
vs = [uv_l.data[li].uv.y for p in mat2_polys for li in p.loop_indices]
print(f"Mat[2] UV bounds: U=[{min(us):.3f}..{max(us):.3f}], V=[{min(vs):.3f}..{max(vs):.3f}]")

for p in mat2_polys[:15]:
    print(f"  Poly {p.index}: center=({p.center.x:.2f},{p.center.y:.2f},{p.center.z:.2f}), uvs={[(round(uv_l.data[li].uv.x,3), round(uv_l.data[li].uv.y,3)) for li in p.loop_indices]}")
