import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

blend_path = r'E:\Agent\TFTF-blender\3rd-party-models\blitzwing_extracted\rar\Blitzwing.blend'
bpy.ops.wm.open_mainfile(filepath=blend_path)
mesh = bpy.data.objects['Blitzwing']

zs = [v.co.z for v in mesh.data.vertices]
ys = [v.co.y for v in mesh.data.vertices]
xs = [v.co.x for v in mesh.data.vertices]
print(f"X range: {min(xs):.4f} to {max(xs):.4f}")
print(f"Y range: {min(ys):.4f} to {max(ys):.4f}")
print(f"Z range: {min(zs):.4f} to {max(zs):.4f}")

# Check vertices in bip_foot_L and bip_toe_L
foot_vg = mesh.vertex_groups.get('bip_foot_L')
toe_vg = mesh.vertex_groups.get('bip_toe_L')
knee_vg = mesh.vertex_groups.get('bip_knee_L')

if foot_vg:
    foot_zs = [v.co.z for v in mesh.data.vertices for g in v.groups if g.group == foot_vg.index]
    print(f"bip_foot_L Z range: {min(foot_zs):.4f} to {max(foot_zs):.4f}")
if toe_vg:
    toe_zs = [v.co.z for v in mesh.data.vertices for g in v.groups if g.group == toe_vg.index]
    print(f"bip_toe_L Z range: {min(toe_zs):.4f} to {max(toe_zs):.4f}")
if knee_vg:
    knee_zs = [v.co.z for v in mesh.data.vertices for g in v.groups if g.group == knee_vg.index]
    print(f"bip_knee_L Z range: {min(knee_zs):.4f} to {max(knee_zs):.4f}")
