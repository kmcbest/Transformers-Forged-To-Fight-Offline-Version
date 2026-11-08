import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
bpy.ops.wm.open_mainfile(filepath=r"E:\Agent\TFTF-blender\3rd-party-models\vortex\weapons\vortex_weapons.blend")
blade = bpy.data.objects["WEP_IonBlade_SKEL.mo_L.dmx"]
uv_layer = blade.data.uv_layers.active
for idx, slot in enumerate(blade.material_slots):
    polys = [p for p in blade.data.polygons if p.material_index == idx]
    uvs = [uv_layer.data[li].uv for p in polys for li in p.loop_indices]
    min_u = min(u[0] for u in uvs)
    max_u = max(u[0] for u in uvs)
    min_v = min(u[1] for u in uvs)
    max_v = max(u[1] for u in uvs)
    print(f"Slot {idx} ({slot.material.name}): U=[{min_u:.3f}, {max_u:.3f}], V=[{min_v:.3f}, {max_v:.3f}]")
