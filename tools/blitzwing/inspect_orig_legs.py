import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

blend_path = r'E:\Agent\TFTF-blender\3rd-party-models\blitzwing_extracted\rar\Blitzwing.blend'
bpy.ops.wm.open_mainfile(filepath=blend_path)

mesh = bpy.data.objects['Blitzwing']
print(f"Original Blitzwing mesh: {mesh.name}, total verts: {len(mesh.data.vertices)}")
print(f"Total vertex groups: {len(mesh.vertex_groups)}")

leg_groups = [vg.name for vg in mesh.vertex_groups if any(k in vg.name.lower() for k in ['foot', 'toe', 'knee', 'leg', 'ankle', 'boot'])]
print("Leg/Foot/Toe vertex groups in original model:")
for g in leg_groups:
    print(" ", g)
