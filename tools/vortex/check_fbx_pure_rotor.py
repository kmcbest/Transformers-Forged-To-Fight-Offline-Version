import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path
import numpy as np

# Load blend to get exact 974 rotor indices
blend_path = Path(r"E:\Agent\TFTF-blender\3rd-party-models\vortex\vehicle\vortex_vehicle.blend")
bpy.ops.wm.open_mainfile(filepath=str(blend_path))
obj = bpy.data.objects.get("VH_Vortex_SKEL.001.dmx")
exact_rotor_vgs = {
    "C_BodyRobo06_XT", "C_BodyRobo16_XT", "C_BodyRobo17_XT",
    "C_BodyRobo18_XT", "C_PropRobo18_XT",
    "C_BodyRobo19_XT", "C_PropRobo19_XT",
    "C_BodyRobo20_XT", "C_PropRobo20_XT",
    "C_BodyRobo21_XT", "C_PropRobo21_XT",
}
rotor_indices = [v.index for v in obj.data.vertices if any(obj.vertex_groups[g.group].name in exact_rotor_vgs and g.weight > 0.5 for g in v.groups)]

# Load FBX
bpy.ops.wm.read_factory_settings(use_empty=True)
fbx_path = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Vortex\vortex_vh_prepared.fbx")
bpy.ops.import_scene.fbx(filepath=str(fbx_path))

for o in bpy.data.objects:
    if o.type == "MESH":
        coords = np.array([o.data.vertices[i].co for i in rotor_indices if i < len(o.data.vertices)])
        print(f"FBX pure rotor vertices count: {len(coords)}")
        print(f"FBX pure rotor center: {coords.mean(axis=0)}")
        print(f"FBX pure rotor X span: [{coords[:,0].min():.2f}, {coords[:,0].max():.2f}]")
        print(f"FBX pure rotor Y span: [{coords[:,1].min():.2f}, {coords[:,1].max():.2f}]")
        print(f"FBX pure rotor Z span: [{coords[:,2].min():.2f}, {coords[:,2].max():.2f}]")
