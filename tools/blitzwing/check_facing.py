import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

blend_path = r'E:\Agent\TFTF-blender\3rd-party-models\blitzwing_extracted\rar\Blitzwing.blend'
bpy.ops.wm.open_mainfile(filepath=blend_path)

mesh = bpy.data.objects['Blitzwing']
# Check nose or face vertices vs back
head_vg = mesh.vertex_groups.get('bip_head')
if head_vg:
    head_vs = [v.co for v in mesh.data.vertices if any(g.group == head_vg.index for g in v.groups)]
    ys = [v.y for v in head_vs]
    print(f"Head Y range: min={min(ys):.3f}, max={max(ys):.3f}")

# Check toe vertices vs heel
toe_vg = mesh.vertex_groups.get('bip_toe_L')
if toe_vg:
    toe_vs = [v.co for v in mesh.data.vertices if any(g.group == toe_vg.index for g in v.groups)]
    ys = [v.y for v in toe_vs]
    print(f"Toe Y range: min={min(ys):.3f}, max={max(ys):.3f}")
