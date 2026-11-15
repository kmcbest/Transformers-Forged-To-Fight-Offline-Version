import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

blend_path = r'E:\Agent\TFTF-blender\3rd-party-models\blitzwing_extracted\rar\Blitzwing.blend'
bpy.ops.wm.open_mainfile(filepath=blend_path)
mesh = bpy.data.objects['Blitzwing']

min_z = min(v.co.z for v in mesh.data.vertices)
SCALE = 1.4803
vgs = set()
for v in mesh.data.vertices:
    scaled_z = (v.co.z - min_z) * SCALE
    if scaled_z <= 0.518:
        for g in v.groups:
            vgs.add(mesh.vertex_groups[g.group].name)

print("Vertex groups of vertices below 0.518m:", sorted(vgs))
