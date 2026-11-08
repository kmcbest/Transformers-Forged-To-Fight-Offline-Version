import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

bpy.ops.wm.open_mainfile(filepath=r"E:\Agent\TFTF-blender\3rd-party-models\vortex\vehicle\vortex_vehicle.blend")
mesh = bpy.data.objects["VH_Vortex_SKEL.001.dmx"]
uv_layer = mesh.data.uv_layers.active
uvs = [uv_layer.data[li].uv for p in mesh.data.polygons for li in p.loop_indices]
print(f"VH UV bounds: U=[{min(u[0] for u in uvs):.3f}, {max(u[0] for u in uvs):.3f}], V=[{min(u[1] for u in uvs):.3f}, {max(u[1] for u in uvs):.3f}]")
