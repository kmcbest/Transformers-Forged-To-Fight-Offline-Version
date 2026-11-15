import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

blend_path = r"E:\Agent\TFTF-blender\3rd-party-models\blitzwing_extracted\rar\Blitzwing.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)

tank = bpy.data.objects['Blitzwing_Alt_Tank']
print("Tank vertices count:", len(tank.data.vertices))
# find vertex with min Y and max Y
min_y_v = min(tank.data.vertices, key=lambda v: v.co.y)
max_y_v = max(tank.data.vertices, key=lambda v: v.co.y)
print("Min Y vertex:", min_y_v.co, "Max Y vertex:", max_y_v.co)

jet = bpy.data.objects['Blitzwing_Jet Mode']
print("Jet vertices count:", len(jet.data.vertices))
min_y_j = min(jet.data.vertices, key=lambda v: v.co.y)
max_y_j = max(jet.data.vertices, key=lambda v: v.co.y)
print("Min Y vertex:", min_y_j.co, "Max Y vertex:", max_y_j.co)
