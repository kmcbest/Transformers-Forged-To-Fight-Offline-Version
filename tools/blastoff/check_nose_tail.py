import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

FBX_PATH = r"O:\agent\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=FBX_PATH)

vh = bpy.data.objects.get("VH_Blastoff_SKEL.mo.dmx")
mw = vh.matrix_world
world_co = [mw @ v.co for v in vh.data.vertices]

# Find vertex with max X and min X
v_max_x = max(world_co, key=lambda v: v.x)
v_min_x = min(world_co, key=lambda v: v.x)

print(f"Vertex at max X: {v_max_x}")
print(f"Vertex at min X: {v_min_x}")

# Count vertices in front half vs back half
mid_x = 0.5 * (min(v.x for v in world_co) + max(v.x for v in world_co))
high_x_verts = [v for v in world_co if v.x > mid_x]
low_x_verts = [v for v in world_co if v.x < mid_x]

# Check Y width at high X vs low X
high_x_y_span = max(v.y for v in high_x_verts) - min(v.y for v in high_x_verts)
low_x_y_span = max(v.y for v in low_x_verts) - min(v.y for v in low_x_verts)

print(f"Y span near high X: {high_x_y_span:.3f}")
print(f"Y span near low X: {low_x_y_span:.3f}")

# Also check wings location:
wing1 = bpy.data.objects.get("VH_BlastoffWing_STAT.mo.001.dmx")
mw_w1 = wing1.matrix_world
w1_xs = [(mw_w1 @ v.co).x for v in wing1.data.vertices]
print(f"Wing X range: [{min(w1_xs):.3f}, {max(w1_xs):.3f}]")
