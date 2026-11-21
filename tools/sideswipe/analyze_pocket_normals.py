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

# Polygons in slot 0 near the pocket
pocket_polys = []
for p in robot.data.polygons:
    if p.material_index == 0:
        uvs = [uv_layer[li].uv for li in p.loop_indices]
        u_avg = sum(u[0] for u in uvs)/len(uvs)
        v_avg = sum(u[1] for u in uvs)/len(uvs)
        if 0.38 <= u_avg <= 0.44 and 0.58 <= v_avg <= 0.66:
            pocket_polys.append(p)

print(f"Pocket polys count: {len(pocket_polys)}")
# Check normals of these pocket polys
# If normals point towards -Y (forward): they are facing the viewer!
facing_forward = [p for p in pocket_polys if p.normal.y < -0.5]
facing_backward = [p for p in pocket_polys if p.normal.y > 0.5]
facing_sideways = [p for p in pocket_polys if abs(p.normal.y) <= 0.5]

print(f"Facing forward (-Y): {len(facing_forward)}")
print(f"Facing backward (+Y): {len(facing_backward)}")
print(f"Facing sideways: {len(facing_sideways)}")

for p in facing_forward[:10]:
    print(f"  Forward pocket poly {p.index}: center={p.center}, normal={p.normal}")
