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

foot_vg = mesh.vertex_groups.get('bip_foot_L')
toe_vg = mesh.vertex_groups.get('bip_toe_L')
knee_vg = mesh.vertex_groups.get('bip_knee_L')

foot_scaled_zs = [(v.co.z - min_z) * SCALE for v in mesh.data.vertices if any(g.group == foot_vg.index for g in v.groups)]
toe_scaled_zs = [(v.co.z - min_z) * SCALE for v in mesh.data.vertices if any(g.group == toe_vg.index for g in v.groups)]
knee_scaled_zs = [(v.co.z - min_z) * SCALE for v in mesh.data.vertices if any(g.group == knee_vg.index for g in v.groups)]

print(f"Foot scaled Z: min={min(foot_scaled_zs):.3f}, max={max(foot_scaled_zs):.3f}")
print(f"Toe scaled Z: min={min(toe_scaled_zs):.3f}, max={max(toe_scaled_zs):.3f}")
print(f"Knee scaled Z: min={min(knee_scaled_zs):.3f}, max={max(knee_scaled_zs):.3f}")

# How many foot vertices are <= 0.518m?
below_0518 = sum(1 for z in foot_scaled_zs if z <= 0.518)
print(f"Foot vertices <= 0.518m: {below_0518} / {len(foot_scaled_zs)}")
