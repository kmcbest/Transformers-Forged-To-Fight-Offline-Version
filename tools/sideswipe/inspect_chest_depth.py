import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

fbx_path = r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\01_source\Sideswipe.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path)

o20 = bpy.data.objects.get("20")
o48 = bpy.data.objects.get("48")

uvl48 = o48.data.uv_layers.active

# Let's inspect polygons in o48 that are within the exact X and Z bounds of Mesh 20
coords20 = [v.co for v in o20.data.vertices]
min_x, max_x = min(c.x for c in coords20), max(c.x for c in coords20)
min_y, max_y = min(c.y for c in coords20), max(c.y for c in coords20)
min_z, max_z = min(c.z for c in coords20), max(c.z for c in coords20)

print(f"Mesh 20: Y is [{min_y:.4f}, {max_y:.4f}]")

# Let's check which polygons of o48 are in front of or behind Mesh 20:
# In Blender FBX: which axis is forward/backward?
# Let's check normals of Mesh 20
for pi, p in enumerate(o20.data.polygons[:5]):
    print(f"Mesh 20 poly {pi}: normal={p.normal}, center={p.center}")

# Polygons in o48 near the same X and Z
polys_in_box = []
for pi, p in enumerate(o48.data.polygons):
    c = p.center
    # Check if inside left or right trapezoid
    # Left: X in [-0.634, -0.15], Z in [0.43, 0.55]
    # Right: X in [0.15, 0.634], Z in [0.43, 0.55]
    if ((-0.634 <= c.x <= -0.15 or 0.15 <= c.x <= 0.634) and
        0.42 <= c.z <= 0.56 and 3.9 <= c.y <= 4.5):
        uvs = [uvl48.data[li].uv for li in p.loop_indices]
        polys_in_box.append((pi, c, p.normal, uvs))

print(f"Total matching polys in o48: {len(polys_in_box)}")
for pi, c, n, uvs in polys_in_box[:10]:
    u_avg = sum(u[0] for u in uvs)/len(uvs)
    v_avg = sum(u[1] for u in uvs)/len(uvs)
    print(f"  o48 poly {pi}: center=({c.x:.3f}, {c.y:.3f}, {c.z:.3f}), norm=({n.x:.3f}, {n.y:.3f}, {n.z:.3f}), uv=({u_avg:.3f}, {v_avg:.3f})")
