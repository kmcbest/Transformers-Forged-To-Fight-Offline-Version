import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

blend_path = r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\01_aligned_mesh\sideswipe_robot_aligned.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)

robot = bpy.data.objects.get("cha_sideswipe_main")
uv_layer = robot.data.uv_layers.active.data

# Polygons that are part of the trapezoid light:
# 1. Existing Slot 1 polys (Mesh 20): 56 polys
# 2. Polygons in Slot 0 that are inside the pocket:
# In world space:
# Left trapezoid: X in [-1.45, -0.55], Y in [-1.30, -0.95], Z in [9.40, 10.05]
# Right trapezoid: X in [0.55, 1.45], Y in [-1.30, -0.95], Z in [9.40, 10.05]

chest_light_polys = []
for p in robot.data.polygons:
    c = p.center
    # Check if Mesh 20 (already mat 1)
    if p.material_index == 1:
        chest_light_polys.append(p.index)
        continue
    # Check if inside left or right trapezoid box and facing forward (normal.y < -0.3)
    if ((0.55 <= abs(c.x) <= 1.45) and
        (-1.28 <= c.y <= -0.95) and
        (9.40 <= c.z <= 10.05) and
        p.normal.y < -0.2):
        # Also check UV: maps to the pocket UV island
        uvs = [uv_layer[li].uv for li in p.loop_indices]
        u_avg = sum(u[0] for u in uvs)/len(uvs)
        v_avg = sum(u[1] for u in uvs)/len(uvs)
        if 0.38 <= u_avg <= 0.44 and 0.58 <= v_avg <= 0.66:
            chest_light_polys.append(p.index)

print(f"Total chest light polys (Mesh 20 + pocket face): {len(chest_light_polys)}")
print(f"Indices: {chest_light_polys}")
