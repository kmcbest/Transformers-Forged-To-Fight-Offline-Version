import os
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import bpy

ROBOT_FBX = r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\01_source\Sideswipe.fbx"
CAR_FBX = r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\01_source\Sideswipe_Car.fbx"

print("=== Loading Robot FBX ===")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=ROBOT_FBX)

for o in bpy.data.objects:
    print(f"Object: {o.name} (type={o.type})")
    if o.type == 'MESH':
        m = o.data
        print(f"  Mesh: {m.name}, verts={len(m.vertices)}, polys={len(m.polygons)}")
        print(f"  Vertex Groups ({len(o.vertex_groups)}): {[vg.name for vg in o.vertex_groups]}")
        print(f"  Materials ({len(m.materials)}): {[mat.name if mat else 'None' for mat in m.materials]}")
        zs = [(o.matrix_world @ v.co).z for v in m.vertices]
        xs = [(o.matrix_world @ v.co).x for v in m.vertices]
        ys = [(o.matrix_world @ v.co).y for v in m.vertices]
        print(f"  Bounds: X=[{min(xs):.3f}, {max(xs):.3f}], Y=[{min(ys):.3f}, {max(ys):.3f}], Z=[{min(zs):.3f}, {max(zs):.3f}]")

    elif o.type == 'ARMATURE':
        arm = o.data
        print(f"  Armature: {arm.name}, bones={len(arm.bones)}")
        for b in arm.bones:
            print(f"    Bone: {b.name}, parent={b.parent.name if b.parent else None}")

print("\n=== Loading Car FBX ===")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=CAR_FBX)

for o in bpy.data.objects:
    print(f"Object: {o.name} (type={o.type})")
    if o.type == 'MESH':
        m = o.data
        print(f"  Mesh: {m.name}, verts={len(m.vertices)}, polys={len(m.polygons)}")
        print(f"  Vertex Groups ({len(o.vertex_groups)}): {[vg.name for vg in o.vertex_groups]}")
        print(f"  Materials ({len(m.materials)}): {[mat.name if mat else 'None' for mat in m.materials]}")
        zs = [(o.matrix_world @ v.co).z for v in m.vertices]
        xs = [(o.matrix_world @ v.co).x for v in m.vertices]
        ys = [(o.matrix_world @ v.co).y for v in m.vertices]
        print(f"  Bounds: X=[{min(xs):.3f}, {max(xs):.3f}], Y=[{min(ys):.3f}, {max(ys):.3f}], Z=[{min(zs):.3f}, {max(zs):.3f}]")
