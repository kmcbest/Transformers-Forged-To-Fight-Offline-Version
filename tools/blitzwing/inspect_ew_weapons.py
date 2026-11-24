import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import bpy
from mathutils import Vector

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r"E:\Agent\TFTF-blender\3rd-party-models\Blitzwing_EW\01_source\H_shandian_G1_M_LOD.fbx")

print("=== Objects in H_shandian_G1_M_LOD.fbx ===")
for obj in bpy.data.objects:
    if obj.type == 'MESH':
        mw = obj.matrix_world
        pts = [mw @ v.co for v in obj.data.vertices]
        xs = [p.x for p in pts]
        ys = [p.y for p in pts]
        zs = [p.z for p in pts]
        mats = [m.name if m else None for m in obj.data.materials]
        vgs = [g.name for g in obj.vertex_groups]
        print(f"  MESH '{obj.name}': verts={len(pts)}, mats={mats}, vgroups={vgs}")
        print(f"    bbox X=[{min(xs):.3f}, {max(xs):.3f}], Y=[{min(ys):.3f}, {max(ys):.3f}], Z=[{min(zs):.3f}, {max(zs):.3f}]")
    elif obj.type == 'ARMATURE':
        print(f"  ARMATURE '{obj.name}': bones={[b.name for b in obj.data.bones]}")
