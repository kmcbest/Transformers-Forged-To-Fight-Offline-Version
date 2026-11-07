import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path
import mathutils

vh_blend = Path(r"E:\Agent\TFTF-blender\3rd-party-models\onslaught\vehicle\onslaught_vehicle.blend")
bpy.ops.wm.open_mainfile(filepath=str(vh_blend))

vh = bpy.data.objects.get("VH.dmx")
bbox = [mathutils.Vector(corner) for corner in vh.bound_box]
min_x = min(v.x for v in bbox)
max_x = max(v.x for v in bbox)
min_y = min(v.y for v in bbox)
max_y = max(v.y for v in bbox)
min_z = min(v.z for v in bbox)
max_z = max(v.z for v in bbox)

print(f"Vehicle bounds:")
print(f"X (length/width): [{min_x:.3f}, {max_x:.3f}] -> size: {max_x - min_x:.3f}m")
print(f"Y (length/width): [{min_y:.3f}, {max_y:.3f}] -> size: {max_y - min_y:.3f}m")
print(f"Z (height): [{min_z:.3f}, {max_z:.3f}] -> size: {max_z - min_z:.3f}m")

# Check which axis is longer: X or Y?
# And where is the front of the truck (cockpit/hood)?
# Let's inspect vertices at extreme X and Y
print(f"Center: ({(min_x+max_x)/2:.3f}, {(min_y+max_y)/2:.3f}, {(min_z+max_z)/2:.3f})")
