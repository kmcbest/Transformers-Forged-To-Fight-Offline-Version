import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
import math
from pathlib import Path

obj_path = Path(r"E:\Agent\RID_game\strongarm_extracted\strongarm_vehicle.obj")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=str(obj_path))

car = bpy.data.objects['strongarm_vehicle']
bpy.context.view_layer.objects.active = car
bpy.ops.mesh.separate(type='LOOSE')

tire = bpy.data.objects['strongarm_vehicle.155']
# Check unique angles around (cy, cz)
verts = tire.data.vertices
cy, cz = 0.601, 1.898
angles = set()
for v in verts:
    dy = v.co.y - cy
    dz = v.co.z - cz
    ang = round(math.atan2(dz, dy) * 180 / math.pi)
    angles.add(ang)

print(f"Circumferential angles in tire ({len(angles)} unique): {sorted(angles)}")
