import bpy
import bmesh
from mathutils import Vector

def check_anatomical_blender(obj, label):
    me = obj.data
    me.calc_normals_split()
    print(f"\n=== Blender {label}: {obj.name} ===")
    # Group polygons by outer +X (x > 1.2)
    px_poly = []
    px_loop = []
    pz_poly = []
    pz_loop = []
    xs = [v.co.x for v in me.vertices]
    ys = [v.co.y for v in me.vertices]
    zs = [v.co.z for v in me.vertices]
    print(f"  Bounds X=[{min(xs):.3f},{max(xs):.3f}] Y=[{min(ys):.3f},{max(ys):.3f}] Z=[{min(zs):.3f},{max(zs):.3f}]")
    max_z = max(zs)
    max_x = max(xs)
    for poly in me.polygons:
        c = poly.center
        if c.x > max_x - 0.35 and abs(poly.normal.x) > 0.5:
            px_poly.append(poly.normal.x)
            for li in poly.loop_indices:
                px_loop.append(me.loops[li].normal.x)
        if abs(c.z - max_z) < 0.45 and abs(poly.normal.z) > 0.5:
            pz_poly.append(poly.normal.z)
            for li in poly.loop_indices:
                pz_loop.append(me.loops[li].normal.z)
    print(f"  Outer +X ({len(px_poly)} polys): poly.n.x avg={sum(px_poly)/max(len(px_poly),1):.3f}, loop.n.x avg={sum(px_loop)/max(len(px_loop),1):.3f}")
    print(f"  Top +Z   ({len(pz_poly)} polys): poly.n.z avg={sum(pz_poly)/max(len(pz_poly),1):.3f}, loop.n.z avg={sum(pz_loop)/max(len(pz_loop),1):.3f}")

# 1. Raw OBJ (note: Blender OBJ importer imports Y-up by default unless axis specified, here let's check both!)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.obj(filepath=r"E:\Agent\RID_game\strongarm_extracted\strongarm_vehicle.obj")
obj_raw = [o for o in bpy.data.objects if o.type == 'MESH'][0]
# Inspect raw OBJ wheel geometry by separating loose parts!
bpy.context.view_layer.objects.active = obj_raw
obj_raw.select_set(True)
# Rotate +90 X to match Blender Z-up just like build_aligned_strongarm_vh.py
obj_raw.rotation_euler = (1.5707963, 0, 0)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
check_anatomical_blender(obj_raw, "Raw OBJ (rotated to Blender Z-up)")

bpy.ops.mesh.separate(type='LOOSE')
parts = [o for o in bpy.data.objects if o.type == 'MESH']
print(f"\nRaw OBJ Loose parts ({len(parts)}):")
for i, p in enumerate(parts):
    vs = [p.matrix_world @ v.co for v in p.data.vertices]
    xs = [v.x for v in vs]; ys = [v.y for v in vs]; zs = [v.z for v in vs]
    cx, cy, cz = (min(xs)+max(xs))/2, (min(ys)+max(ys))/2, (min(zs)+max(zs))/2
    sx, sy, sz = max(xs)-min(xs), max(ys)-min(ys), max(zs)-min(zs)
    print(f"  Part[{i:2d}] verts={len(vs):4d} center=({cx:+.3f},{cy:+.3f},{cz:+.3f}) size=({sx:.3f},{sy:.3f},{sz:.3f})")

# 2. Check Current VH FBX and Current Robot FBX
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Strongarm\strongarm_vh_prepared.fbx")
for o in bpy.data.objects:
    if o.type == 'MESH':
        check_anatomical_blender(o, "Current VH FBX")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Strongarm\strongarm_prepared.fbx")
for o in bpy.data.objects:
    if o.type == 'MESH':
        check_anatomical_blender(o, "Current Robot FBX")
