import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path
import numpy as np

blend_path = Path(r"E:\Agent\TFTF-blender\3rd-party-models\vortex\vehicle\vortex_vehicle.blend")
bpy.ops.wm.open_mainfile(filepath=str(blend_path))

obj = bpy.data.objects.get("VH_Vortex_SKEL.001.dmx")

exact_rotor_vgs = {
    "C_BodyRobo06_XT",
    "C_BodyRobo16_XT",
    "C_BodyRobo17_XT",
    "C_BodyRobo18_XT",
    "C_PropRobo18_XT",
    "C_BodyRobo19_XT",
    "C_PropRobo19_XT",
    "C_BodyRobo20_XT",
    "C_PropRobo20_XT",
    "C_BodyRobo21_XT",
    "C_PropRobo21_XT",
}

rotor_indices = set()
for v in obj.data.vertices:
    for g in v.groups:
        vg_name = obj.vertex_groups[g.group].name
        if vg_name in exact_rotor_vgs and g.weight > 0.5:
            rotor_indices.add(v.index)
            break

print(f"Total pure rotor vertices: {len(rotor_indices)}")
rotor_coords = np.array([obj.data.vertices[i].co for i in rotor_indices])
print(f"X bounds: [{rotor_coords[:,0].min():.2f}, {rotor_coords[:,0].max():.2f}] (span={rotor_coords[:,0].max()-rotor_coords[:,0].min():.2f})")
print(f"Y bounds: [{rotor_coords[:,1].min():.2f}, {rotor_coords[:,1].max():.2f}] (span={rotor_coords[:,1].max()-rotor_coords[:,1].min():.2f})")
print(f"Z bounds: [{rotor_coords[:,2].min():.2f}, {rotor_coords[:,2].max():.2f}] (span={rotor_coords[:,2].max()-rotor_coords[:,2].min():.2f})")
print(f"Pure rotor center in Blender: {rotor_coords.mean(axis=0)}")

# Check hub center only (VG 0, 1, 2)
hub_vgs = {"C_BodyRobo06_XT", "C_BodyRobo16_XT", "C_BodyRobo17_XT"}
hub_indices = set()
for v in obj.data.vertices:
    for g in v.groups:
        vg_name = obj.vertex_groups[g.group].name
        if vg_name in hub_vgs and g.weight > 0.5:
            hub_indices.add(v.index)
            break

hub_coords = np.array([obj.data.vertices[i].co for i in hub_indices])
print(f"Hub vertices: {len(hub_indices)}, Hub center in Blender: {hub_coords.mean(axis=0)}")
