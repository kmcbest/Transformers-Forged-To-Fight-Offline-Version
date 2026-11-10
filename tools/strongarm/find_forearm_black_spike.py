import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

# 1. Check Strongarm.fbx objects in Left forearm/wrist zone and their materials + vgroups
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r"E:\Agent\RID_game\strongarm_zip_extracted\source\Strongarm.fbx")
for o in sorted(bpy.data.objects, key=lambda x: x.name):
    if o.type == 'MESH' and "_l" in o.name.lower():
        if any(k in o.name.lower() for k in ("arm", "palm", "hand", "elbow", "light")):
            mat = o.material_slots[0].material.name if o.material_slots and o.material_slots[0].material else "NONE"
            vgs = sorted({o.vertex_groups[g.group].name for v in o.data.vertices for g in v.groups if g.weight > 0.05})
            print(f"Raw {o.name:24s}: mat={mat:15s} verts={len(o.data.vertices):4d} vgs={vgs}")

# 2. Check current strongarm_prepared.fbx Left palm vertices: which vertices have Z > 4.25 and what weights they actually ended up with!
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Strongarm\strongarm_prepared.fbx")
mesh = next(o for o in bpy.data.objects if o.type == 'MESH')
by_b = {}
for v in mesh.data.vertices:
    if v.co.x > 1.7 and 4.20 < v.co.z < 4.90:
        wstr = ", ".join(f"{mesh.vertex_groups[g.group].name}:{g.weight:.2f}" for g in v.groups if g.weight > 0.05)
        by_b[wstr] = by_b.get(wstr, 0) + 1
print("\n=== strongarm_prepared.fbx Left forearm/wrist (X>1.7, 4.20<Z<4.90) exact weight combos ===")
for k, c in sorted(by_b.items(), key=lambda x: -x[1])[:20]:
    print(f"  count={c:4d} weights=[{k}]")
