import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

# Open the exported FBX or inspect baked parts
bpy.ops.wm.open_mainfile(filepath=r"E:\Agent\TFTF-blender\3rd-party-models\vortex\vortex_master.blend")
# Let's inspect where min_z comes from
for obj in bpy.data.objects:
    if obj.type == 'MESH':
        zs = [v.co.z for v in obj.data.vertices]
        print(f"Mesh {obj.name}: min Z = {min(zs):.3f}, max Z = {max(zs):.3f}")
