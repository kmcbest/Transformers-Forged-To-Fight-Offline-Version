import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path
from mathutils import Vector
import numpy as np

blend_path = Path(r"E:\Agent\TFTF-blender\3rd-party-models\vortex\vehicle\vortex_vehicle.blend")
bpy.ops.wm.open_mainfile(filepath=str(blend_path))

obj = bpy.data.objects.get("VH_Vortex_SKEL.001.dmx")

# Find vertices in rotor vertex groups: 0 to 10
rotor_vgs = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
rotor_verts_co = []
body_verts_co = []

for v in obj.data.vertices:
    is_rotor = False
    for g in v.groups:
        if g.group in rotor_vgs and g.weight > 0.5:
            is_rotor = True
            break
    co = obj.matrix_world @ v.co
    if is_rotor:
        rotor_verts_co.append(co)
    else:
        body_verts_co.append(co)

rotor_verts_co = np.array(rotor_verts_co)
print(f"Total rotor vertices: {len(rotor_verts_co)}")
print(f"Blender raw rotor center: {rotor_verts_co.mean(axis=0)}")

# Transform applied in BuildVortexInspectionScene.cs:
# newVerts[vi] = new Vector3(-v.x, v.z + dy, v.y + dz);
# where dy = 0.60, dz = -1.50
# Note: v in Unity rawMesh was imported from FBX.
# In Blender, export FBX: Blender coords (x, y, z) become Unity coords?
# Let's check how Blender FBX exporter maps coordinates!
