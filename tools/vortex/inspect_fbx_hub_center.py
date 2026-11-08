import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path
import numpy as np

# Load vortex_vehicle.blend to get the 974 rotor vertex indices
blend_path = Path(r"E:\Agent\TFTF-blender\3rd-party-models\vortex\vehicle\vortex_vehicle.blend")
bpy.ops.wm.open_mainfile(filepath=str(blend_path))

obj = bpy.data.objects.get("VH_Vortex_SKEL.001.dmx")
rotor_vgs = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
hub_vgs = [0, 1, 2]

rotor_indices = set()
hub_indices = set()
for v in obj.data.vertices:
    for g in v.groups:
        if g.group in rotor_vgs and g.weight > 0.5:
            rotor_indices.add(v.index)
            if g.group in hub_vgs:
                hub_indices.add(v.index)
            break

print(f"Rotor indices count: {len(rotor_indices)}, Hub indices count: {len(hub_indices)}")

# Now load vortex_vh_prepared.fbx
bpy.ops.wm.read_factory_settings(use_empty=True)
fbx_path = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Vortex\vortex_vh_prepared.fbx")
bpy.ops.import_scene.fbx(filepath=str(fbx_path))

for o in bpy.data.objects:
    if o.type == "MESH":
        print(f"FBX Mesh: {o.name}, verts: {len(o.data.vertices)}")
        # Check coordinates of hub vertices
        hub_coords = [o.data.vertices[i].co for i in hub_indices if i < len(o.data.vertices)]
        hub_coords = np.array(hub_coords)
        print(f"Hub center in FBX: {hub_coords.mean(axis=0)}")
        rotor_coords = [o.data.vertices[i].co for i in rotor_indices if i < len(o.data.vertices)]
        rotor_coords = np.array(rotor_coords)
        print(f"Rotor center in FBX: {rotor_coords.mean(axis=0)}")
