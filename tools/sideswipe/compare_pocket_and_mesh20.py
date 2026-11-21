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

# Find all polygons in Slot 0 that map to the left or right red/black pocket
# From the crop, X=847, Y=788 -> U in [0.38, 0.45], V in [0.58, 0.65]
pocket_polys = []
for pi, p in enumerate(robot.data.polygons):
    if p.material_index == 0:
        uvs = [uv_layer[li].uv for li in p.loop_indices]
        u_avg = sum(u[0] for u in uvs)/len(uvs)
        v_avg = sum(u[1] for u in uvs)/len(uvs)
        # Check if in the left or right pocket UVs
        if 0.35 <= u_avg <= 0.46 and 0.55 <= v_avg <= 0.67:
            pocket_polys.append((pi, p, uvs, "Left_Pocket_Tex"))
        # Check if there is another symmetric pocket on the texture
        # Let's search other UV ranges

print(f"Polygons mapping to pocket UV (0.41, 0.61): {len(pocket_polys)}")
for pi, p, uvs, tag in pocket_polys:
    c = p.center
    print(f"  Poly {pi}: center=({c.x:.3f}, {c.y:.3f}, {c.z:.3f}), norm=({p.normal.x:.3f}, {p.normal.y:.3f}, {p.normal.z:.3f})")

# Now let's compare their 3D coordinates with Slot 1 (Mesh 20)
slot1_polys = [p for p in robot.data.polygons if p.material_index == 1]
print(f"\nSlot 1 (Mesh 20) polys: {len(slot1_polys)}")
for pi, p in enumerate(slot1_polys[:10]):
    c = p.center
    print(f"  Slot 1 poly {pi}: center=({c.x:.3f}, {c.y:.3f}, {c.z:.3f}), norm=({p.normal.x:.3f}, {p.normal.y:.3f}, {p.normal.z:.3f})")
