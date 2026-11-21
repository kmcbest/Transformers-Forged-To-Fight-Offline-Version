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

# Find all polygons in Slot 0 that map to the pocket texture
pocket_polys = []
for p in robot.data.polygons:
    if p.material_index == 0:
        uvs = [uv_layer[li].uv for li in p.loop_indices]
        u_avg = sum(u[0] for u in uvs)/len(uvs)
        v_avg = sum(u[1] for u in uvs)/len(uvs)
        if 0.38 <= u_avg <= 0.44 and 0.58 <= v_avg <= 0.66:
            pocket_polys.append(p)

print(f"Total pocket polys in Slot 0: {len(pocket_polys)}")

# Where are these pocket polys?
for p in pocket_polys:
    uvs = [uv_layer[li].uv for li in p.loop_indices]
    u_avg = sum(u[0] for u in uvs)/len(uvs)
    v_avg = sum(u[1] for u in uvs)/len(uvs)
    print(f"Poly {p.index}: center={p.center}, norm={p.normal}, uv=({u_avg:.3f}, {v_avg:.3f})")
