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

print(f"Scanning polygons in trapezoid region...")
left_trapezoid_polys = []
right_trapezoid_polys = []

for pi, p in enumerate(robot.data.polygons):
    c = p.center
    # In world/blend coords:
    # Right side of chest (from viewer's perspective: X > 0, actually character's left or right):
    # Let's check X in [0.4, 1.5], Z in [9.3, 10.1], Y in [-1.5, -0.8]
    if (0.3 <= abs(c.x) <= 1.5 and 9.3 <= c.z <= 10.1 and -1.5 <= c.y <= -0.8):
        uvs = [uv_layer[li].uv for li in p.loop_indices]
        u_avg = sum(u[0] for u in uvs)/len(uvs)
        v_avg = sum(u[1] for u in uvs)/len(uvs)
        if c.x < 0:
            left_trapezoid_polys.append((pi, p.material_index, c, p.normal, (u_avg, v_avg)))
        else:
            right_trapezoid_polys.append((pi, p.material_index, c, p.normal, (u_avg, v_avg)))

print(f"Left trapezoid polys: {len(left_trapezoid_polys)}, Right trapezoid polys: {len(right_trapezoid_polys)}")

print("\n--- LEFT TRAPEZOID POLYS (X < 0) ---")
for pi, mi, c, n, uv in sorted(left_trapezoid_polys, key=lambda x: x[2].y): # Sort by Y (front to back)
    print(f"Poly {pi}: Mat={mi}, center=({c.x:.3f}, {c.y:.3f}, {c.z:.3f}), norm=({n.x:.3f}, {n.y:.3f}, {n.z:.3f}), uv=({uv[0]:.3f}, {uv[1]:.3f})")

print("\n--- RIGHT TRAPEZOID POLYS (X > 0) ---")
for pi, mi, c, n, uv in sorted(right_trapezoid_polys, key=lambda x: x[2].y):
    print(f"Poly {pi}: Mat={mi}, center=({c.x:.3f}, {c.y:.3f}, {c.z:.3f}), norm=({n.x:.3f}, {n.y:.3f}, {n.z:.3f}), uv=({uv[0]:.3f}, {uv[1]:.3f})")
