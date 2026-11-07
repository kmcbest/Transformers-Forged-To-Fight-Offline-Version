import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path

vh_blend = Path(r"E:\Agent\TFTF-blender\3rd-party-models\onslaught\vehicle\onslaught_vehicle.blend")
bpy.ops.wm.open_mainfile(filepath=str(vh_blend))

vh = bpy.data.objects.get("VH.dmx")

# Check polygons at extreme +X vs -X
verts = vh.data.vertices
max_x_verts = [v.co for v in verts if v.co.x > 1.8]
min_x_verts = [v.co for v in verts if v.co.x < -2.5]

print(f"Number of verts at extreme +X (>1.8): {len(max_x_verts)}, Z range: [{min(v.z for v in max_x_verts):.2f}, {max(v.z for v in max_x_verts):.2f}]")
print(f"Number of verts at extreme -X (<-2.5): {len(min_x_verts)}, Z range: [{min(v.z for v in min_x_verts):.2f}, {max(v.z for v in min_x_verts):.2f}]")

# Check bone names in Onslaught_VH_ARM
vh_arm = bpy.data.objects.get("Onslaught_VH_ARM")
for b in vh_arm.data.bones:
    if any(k in b.name.lower() for k in ["wheel", "cab", "front", "back", "hood", "window"]):
        print(f"Bone: {b.name}, head={b.head_local}")
