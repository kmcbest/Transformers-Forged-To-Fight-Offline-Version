import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Let's inspect what happens in build_aligned_blitzwing.py to LeftFoot
import bpy

blend_path = r'E:\Agent\TFTF-blender\3rd-party-models\blitzwing_extracted\rar\Blitzwing.blend'
bpy.ops.wm.open_mainfile(filepath=blend_path)
mesh = bpy.data.objects['Blitzwing']

min_z = min(v.co.z for v in mesh.data.vertices)
SCALE = 1.4803
BOOT_Z_THRESH = 0.35 * SCALE # ~0.518m

old_vg_by_index = {vg.index: vg.name for vg in mesh.vertex_groups}
left_foot_weights = 0
for v in mesh.data.vertices:
    vi = v.index
    vz = (v.co.z - min_z) * SCALE
    is_left_shin_or_foot = any(old_vg_by_index.get(g.group) in ["bip_knee_L", "bip_foot_L", "bip_toe_L"] for g in v.groups)
    if is_left_shin_or_foot and vz > BOOT_Z_THRESH:
        continue
    for g in v.groups:
        old_vg_name = old_vg_by_index.get(g.group)
        if old_vg_name == "bip_foot_L":
            left_foot_weights += 1

print(f"Number of vertices below 0.518m with bip_foot_L: {left_foot_weights}")
