import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

bpy.ops.wm.open_mainfile(filepath=r"E:\Agent\TFTF-blender\3rd-party-models\vortex\weapons\vortex_weapons.blend")
blade = bpy.data.objects["WEP_IonBlade_SKEL.mo_L.dmx"]
for idx, slot in enumerate(blade.material_slots):
    polys = [p for p in blade.data.polygons if p.material_index == idx]
    print(f"Slot {idx}: {slot.material.name if slot.material else 'None'} -> {len(polys)} polys")
    uv_layer = blade.data.uv_layers.active
    uvs = [uv_layer.data[li].uv for p in polys[:3] for li in p.loop_indices]
    print(f"   UV sample: {[(round(u[0], 3), round(u[1], 3)) for u in uvs[:4]]}")
