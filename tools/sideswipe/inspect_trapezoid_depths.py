import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

blend_path = r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\01_aligned_mesh\sideswipe_robot_aligned.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)

robot = bpy.data.objects.get("cha_sideswipe_main")

# Let's inspect the polygons in Slot 0 that overlap with Slot 1
# Let's create a temporary object with just the trapezoid polygons:
# Material 0 polygons near trapezoid, and Material 1 polygons
uv_layer = robot.data.uv_layers.active.data

slot1_polys = [p.index for p in robot.data.polygons if p.material_index == 1]
slot0_pocket_polys = []
for p in robot.data.polygons:
    if p.material_index == 0:
        uvs = [uv_layer[li].uv for li in p.loop_indices]
        u_avg = sum(u[0] for u in uvs)/len(uvs)
        v_avg = sum(u[1] for u in uvs)/len(uvs)
        if 0.38 <= u_avg <= 0.44 and 0.58 <= v_avg <= 0.66:
            slot0_pocket_polys.append(p.index)

print(f"Slot 1 poly count: {len(slot1_polys)}")
print(f"Slot 0 pocket poly count: {len(slot0_pocket_polys)}")

# Let's check their vertex indices and coordinates
p0_coords = []
for pi in slot0_pocket_polys:
    p = robot.data.polygons[pi]
    for vi in p.vertices:
        p0_coords.append(robot.data.vertices[vi].co)

p1_coords = []
for pi in slot1_polys:
    p = robot.data.polygons[pi]
    for vi in p.vertices:
        p1_coords.append(robot.data.vertices[vi].co)

print(f"Slot 0 pocket Y min/max: {min(c.y for c in p0_coords):.4f} to {max(c.y for c in p0_coords):.4f}")
print(f"Slot 1 (Mesh 20) Y min/max: {min(c.y for c in p1_coords):.4f} to {max(c.y for c in p1_coords):.4f}")
