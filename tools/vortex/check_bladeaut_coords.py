import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

bpy.ops.wm.open_mainfile(filepath=r"E:\Agent\TFTF-blender\3rd-party-models\vortex\weapons\vortex_weapons.blend")
blade = bpy.data.objects["WEP_IonBlade_SKEL.mo_L.dmx"]
polys = [p for p in blade.data.polygons if p.material_index == 1]
v_indices = {v for p in polys for v in p.vertices}
coords = [blade.data.vertices[v].co for v in v_indices]
print(f"BladeAut {len(coords)} verts: X=[{min(c.x for c in coords):.3f}, {max(c.x for c in coords):.3f}], Y=[{min(c.y for c in coords):.3f}, {max(c.y for c in coords):.3f}], Z=[{min(c.z for c in coords):.3f}, {max(c.z for c in coords):.3f}]")
