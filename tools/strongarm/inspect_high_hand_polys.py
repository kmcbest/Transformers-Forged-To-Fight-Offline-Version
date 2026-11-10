import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

# Test posing arm + wrist in Blender using strongarm_prepared.fbx to see WHICH vertices poke through arm_geo's white box!
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Strongarm\strongarm_prepared.fbx")
mesh = next(o for o in bpy.data.objects if o.type == 'MESH')

# Find all polygons with ANY vertex weighted > 0.05 to LeftHand or LeftHandThumb1 that have Z > 4.30 in rest pose!
print("=== Polygons with Hand/Thumb weights at Z > 4.30 in strongarm_prepared.fbx ===")
for p in mesh.data.polygons:
    max_z = max(mesh.data.vertices[vi].co.z for vi in p.vertices)
    if max_z > 4.30:
        bnames = set()
        for vi in p.vertices:
            v = mesh.data.vertices[vi]
            if v.co.x > 1.7:
                for g in v.groups:
                    if g.weight > 0.05:
                        bnames.add(mesh.vertex_groups[g.group].name)
        if any("Hand" in b for b in bnames):
            xs = [mesh.data.vertices[vi].co.x for vi in p.vertices]
            ys = [mesh.data.vertices[vi].co.y for vi in p.vertices]
            zs = [mesh.data.vertices[vi].co.z for vi in p.vertices]
            if len(xs) and max(xs) > 1.7:
                print(f"  poly[{p.index:5d}] X=[{min(xs):.3f},{max(xs):.3f}] Y=[{min(ys):.3f},{max(ys):.3f}] Z=[{min(zs):.3f},{max(zs):.3f}] bones={sorted(bnames)}")
