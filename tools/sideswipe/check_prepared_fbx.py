import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import bpy

FBX_PREP = r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\03_fbx_exports\sideswipe_robot_prepared.fbx"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=FBX_PREP)

o = bpy.data.objects.get("cha_sideswipe_main")
# Find red headlight vertices (remapped to U around 0.31 or 0.445, V=0.56)
uvl = o.data.uv_layers.active
chest_verts = set()
for poly in o.data.polygons:
    for li in poly.loop_indices:
        u, v = uvl.data[li].uv
        if abs(v - 0.56) < 0.05 and (abs(u - 0.31) < 0.05 or abs(u - 0.445) < 0.05):
            for vi in poly.vertices:
                chest_verts.add(vi)

if chest_verts:
    c_pts = [o.data.vertices[vi].co for vi in chest_verts]
    print(f"Chest headlights (red lights) count={len(chest_verts)}, mean=({sum(p.x for p in c_pts)/len(c_pts):.3f}, {sum(p.y for p in c_pts)/len(c_pts):.3f}, {sum(p.z for p in c_pts)/len(c_pts):.3f})")

# Let's check max Y and min Y of all vertices
ys = [v.co.y for v in o.data.vertices]
print(f"Y range in prepared FBX: [{min(ys):.3f}, {max(ys):.3f}]")
