import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path

blend_path = Path(r"E:\Agent\TFTF-blender\3rd-party-models\vortex\vehicle\vortex_vehicle.blend")
bpy.ops.wm.open_mainfile(filepath=str(blend_path))

for obj in bpy.data.objects:
    if obj.type == 'MESH':
        print(f"Object: {obj.name}")
        # Find rotor vertices vs body vertices
        rotor_vgs = [vg.name for vg in obj.vertex_groups if "prop" in vg.name.lower()]
        print(f"Rotor vertex groups: {rotor_vgs}")
        for vg_name in rotor_vgs[:2]:
            vg = obj.vertex_groups[vg_name]
            r_verts = [v.co for v in obj.data.vertices if any(g.group == vg.index for g in v.groups)]
            if r_verts:
                xs = [v.x for v in r_verts]
                ys = [v.y for v in r_verts]
                zs = [v.z for v in r_verts]
                print(f"  {vg_name}: X=[{min(xs):.2f}, {max(xs):.2f}], Y=[{min(ys):.2f}, {max(ys):.2f}], Z=[{min(zs):.2f}, {max(zs):.2f}]")
        
        # Check all vertices bounds
        xs = [v.co.x for v in obj.data.vertices]
        ys = [v.co.y for v in obj.data.vertices]
        zs = [v.co.z for v in obj.data.vertices]
        print(f"All verts: X=[{min(xs):.2f}, {max(xs):.2f}], Y=[{min(ys):.2f}, {max(ys):.2f}], Z=[{min(zs):.2f}, {max(zs):.2f}]")
