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
coords20 = [v.co for v in o20.data.vertices]
min_x, max_x = min(c.x for c in coords20), max(c.x for c in coords20)
min_y, max_y = min(c.y for c in coords20), max(c.y for c in coords20)
min_z, max_z = min(c.z for c in coords20), max(c.z for c in coords20)

print(f"Mesh 20 bounds: X=[{min_x:.3f}, {max_x:.3f}], Y=[{min_y:.3f}, {max_y:.3f}], Z=[{min_z:.3f}, {max_z:.3f}]")

for o in bpy.data.objects:
    if o.type == 'MESH' and o.name != "20":
        overlapping_polys = []
        for pi, poly in enumerate(o.data.polygons):
            poly_coords = [o.data.vertices[vi].co for vi in poly.vertices]
            px = [c.x for c in poly_coords]
            py = [c.y for c in poly_coords]
            pz = [c.z for c in poly_coords]
            # Check overlap in X, Y, Z
            if (max(px) >= min_x - 0.1 and min(px) <= max_x + 0.1 and
                max(py) >= min_y - 0.1 and min(py) <= max_y + 0.1 and
                max(pz) >= min_z - 0.1 and min(pz) <= max_z + 0.1):
                overlapping_polys.append((pi, poly_coords))
        if overlapping_polys:
            print(f"Object '{o.name}' has {len(overlapping_polys)} overlapping polygons near Mesh 20!")
            # Sample a few overlapping polygons
            for pi, coords in overlapping_polys[:5]:
                avg_co = [sum(c[i] for c in coords)/len(coords) for i in range(3)]
                print(f"   Poly {pi}: avg={avg_co}")
