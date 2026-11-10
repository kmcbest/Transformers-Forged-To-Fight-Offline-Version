import sys
import bpy
import bmesh
from mathutils import Vector

def analyze_mesh(obj, label):
    me = obj.data
    me.calc_normals_split()
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    center = sum((v.co for v in bm.verts), Vector()) / max(len(bm.verts), 1)
    out_fn = 0
    in_fn = 0
    dot_fn_vn = []
    for f in bm.faces:
        c = f.calc_center_median() - center
        if c.dot(f.normal) >= 0:
            out_fn += 1
        else:
            in_fn += 1
    # Check loop split normals vs polygon normal
    neg_loop = 0
    pos_loop = 0
    for poly in me.polygons:
        for li in poly.loop_indices:
            d = poly.normal.dot(me.loops[li].normal)
            if d < 0:
                neg_loop += 1
            else:
                pos_loop += 1
    xs = [v.co.x for v in bm.verts]
    ys = [v.co.y for v in bm.verts]
    zs = [v.co.z for v in bm.verts]
    print(f"\n=== {label}: {obj.name} verts={len(bm.verts)} faces={len(bm.faces)} ===")
    print(f"  Bounds X=[{min(xs):.3f},{max(xs):.3f}] Y=[{min(ys):.3f},{max(ys):.3f}] Z=[{min(zs):.3f},{max(zs):.3f}]")
    print(f"  Outward Face Normals: out={out_fn}, in={in_fn}")
    print(f"  Loop vs Poly Normal: pos={pos_loop}, neg={neg_loop}")
    print(f"  Has custom split normals: {me.has_custom_normals}, use_auto_smooth: {me.use_auto_smooth}")
    bm.free()

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.obj(filepath=r"E:\Agent\RID_game\strongarm_extracted\strongarm_vehicle.obj")
for o in bpy.data.objects:
    if o.type == 'MESH':
        analyze_mesh(o, "Raw OBJ")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Strongarm\strongarm_vh_prepared.fbx")
for o in bpy.data.objects:
    if o.type == 'MESH':
        analyze_mesh(o, "Current VH FBX")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Strongarm\strongarm_prepared.fbx")
for o in bpy.data.objects:
    if o.type == 'MESH':
        analyze_mesh(o, "Current Robot FBX")
