import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

bpy.ops.wm.open_mainfile(filepath=r"E:\Agent\TFTF-blender\3rd-party-models\Brawl\01_aligned_mesh\brawl_tank_aligned.blend")
obj = bpy.data.objects.get("VH_BrawlCINE_SKEL.001.dmx")

print(f"Brawl Tank Vertices: {len(obj.data.vertices)}")
print(f"Materials ({len(obj.material_slots)}): {[s.material.name for s in obj.material_slots]}")

poly_mat_counts = {}
for p in obj.data.polygons:
    poly_mat_counts[p.material_index] = poly_mat_counts.get(p.material_index, 0) + 1

for midx, count in poly_mat_counts.items():
    mname = obj.material_slots[midx].material.name if midx < len(obj.material_slots) else "Unknown"
    print(f"  Material [{midx}] '{mname}': {count} polygons")
