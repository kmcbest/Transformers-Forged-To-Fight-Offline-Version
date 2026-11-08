import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path
from mathutils import Vector
import numpy as np
import json

# 1. Get raw rotor center in Blender
blend_path = Path(r"E:\Agent\TFTF-blender\3rd-party-models\vortex\vehicle\vortex_vehicle.blend")
bpy.ops.wm.open_mainfile(filepath=str(blend_path))

obj = bpy.data.objects.get("VH_Vortex_SKEL.001.dmx")
rotor_vgs = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
hub_vgs = [0, 1, 2] # Cap, shaft, mast/hub

rotor_pts = []
hub_pts = []
for v in obj.data.vertices:
    for g in v.groups:
        if g.group in rotor_vgs and g.weight > 0.5:
            rotor_pts.append(v.co)
            if g.group in hub_vgs:
                hub_pts.append(v.co)
            break

hub_pts = np.array(hub_pts)
rotor_pts = np.array(rotor_pts)
print(f"Hub verts: {len(hub_pts)}, Rotor verts: {len(rotor_pts)}")
raw_hub_center = hub_pts.mean(axis=0)
print(f"Raw hub center in Blender: {raw_hub_center}")

# In BuildVortexInspectionScene.cs:
# newVerts[vi] = new Vector3(-v.x, v.z + dy, v.y + dz)
# dy = 0.60, dz = -1.50
# Note: FBX export from Blender applies coordinate conversion:
# In Blender export FBX: default is -Z forward, Y up.
# Let's inspect what rawMesh.vertices in Unity actually were!
