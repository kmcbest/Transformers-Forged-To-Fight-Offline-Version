import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

BLEND_PATH = r"E:\Agent\TFTF-blender\3rd-party-models\BlastOff\01_aligned_mesh\blastoff_jet_aligned.blend"

bpy.ops.wm.open_mainfile(filepath=BLEND_PATH)

veh = bpy.data.objects.get("cha_blastoff_gs_01")
mw = veh.matrix_world
verts = [mw @ v.co for v in veh.data.vertices]

min_y_v = min(verts, key=lambda v: v.y)
max_y_v = max(verts, key=lambda v: v.y)

print(f"Blast Off Vehicle in Blender:")
print(f"  Min Y vertex (closest to camera at Y=-22): {min_y_v}")
print(f"  Max Y vertex (furthest from camera):       {max_y_v}")

# Let's check X span at Min Y vs Max Y:
near_min_y = [v for v in verts if v.y < -3.0]
near_max_y = [v for v in verts if v.y > 3.0]

print(f"X span at Min Y (front): {max(v.x for v in near_min_y) - min(v.x for v in near_min_y):.3f}")
print(f"X span at Max Y (back):  {max(v.x for v in near_max_y) - min(v.x for v in near_max_y):.3f}")
