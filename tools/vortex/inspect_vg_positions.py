import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path
from mathutils import Vector

blend_path = Path(r"E:\Agent\TFTF-blender\3rd-party-models\vortex\vehicle\vortex_vehicle.blend")
bpy.ops.wm.open_mainfile(filepath=str(blend_path))

obj = bpy.data.objects.get("VH_Vortex_SKEL.001.dmx")
if obj:
    for vg in obj.vertex_groups:
        coords = [obj.matrix_world @ v.co for v in obj.data.vertices for g in v.groups if g.group == vg.index and g.weight > 0.1]
        if coords:
            min_x = min(c.x for c in coords)
            max_x = max(c.x for c in coords)
            min_y = min(c.y for c in coords)
            max_y = max(c.y for c in coords)
            min_z = min(c.z for c in coords)
            max_z = max(c.z for c in coords)
            center = Vector(((min_x+max_x)/2, (min_y+max_y)/2, (min_z+max_z)/2))
            print(f"VG [{vg.index:2d}] {vg.name:18s}: {len(coords):4d} v | center=({center.x:6.2f}, {center.y:6.2f}, {center.z:6.2f}) | span=({max_x-min_x:5.2f}, {max_y-min_y:5.2f}, {max_z-min_z:5.2f})")
