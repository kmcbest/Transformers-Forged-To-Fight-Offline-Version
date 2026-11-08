import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path

blend_path = Path(r"E:\Agent\TFTF-blender\3rd-party-models\vortex\vehicle\vortex_vehicle.blend")
bpy.ops.wm.open_mainfile(filepath=str(blend_path))

obj = bpy.data.objects["VH_Vortex_SKEL.001.dmx"]
for vg in obj.vertex_groups:
    v_indices = [v.index for v in obj.data.vertices if any(g.group == vg.index for g in v.groups)]
    if not v_indices: continue
    xs = [obj.data.vertices[i].co.x for i in v_indices]
    ys = [obj.data.vertices[i].co.y for i in v_indices]
    zs = [obj.data.vertices[i].co.z for i in v_indices]
    if any(k in vg.name.lower() for k in ["tail", "fin", "head", "nose", "wing", "prop", "cockpit", "rotor"]):
        print(f"VG {vg.name:25s}: count={len(v_indices):4d} | X=[{min(xs):5.2f}, {max(xs):5.2f}] Y=[{min(ys):5.2f}, {max(ys):5.2f}] Z=[{min(zs):5.2f}, {max(zs):5.2f}]")
