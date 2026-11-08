import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path

blend_path = Path(r"E:\Agent\TFTF-blender\3rd-party-models\vortex\vehicle\vortex_vehicle.blend")
bpy.ops.wm.open_mainfile(filepath=str(blend_path))
vh_mesh = bpy.data.objects["VH_Vortex_SKEL.001.dmx"]

prop18_vg = vh_mesh.vertex_groups.get("C_PropRobo18_XT")
print("C_PropRobo18_XT VG index:", prop18_vg.index if prop18_vg else "None")

# Find vertices that have C_PropRobo18_XT
found = 0
for v in vh_mesh.data.vertices:
    for g in v.groups:
        if g.group == prop18_vg.index:
            found += 1
            if found <= 3:
                # get group name via mesh.vertex_groups[g.group].name
                actual_name = vh_mesh.vertex_groups[g.group].name
                print(f"Vert {v.index}: g.group={g.group}, actual_name={actual_name}")

print(f"Total verts with prop18: {found}")

