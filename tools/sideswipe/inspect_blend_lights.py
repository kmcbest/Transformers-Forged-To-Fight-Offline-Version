import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

blend_path = r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\01_aligned_mesh\sideswipe_robot_aligned.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)

robot = bpy.data.objects.get("cha_sideswipe_cin_rotf_00") or bpy.data.objects.get("Sideswipe_Robot")
if not robot:
    for o in bpy.data.objects:
        if o.type == 'MESH':
            robot = o
            break

print("Found robot object:", robot.name)
print("Materials on robot:", [m.name for m in robot.data.materials])
uv_layer = robot.data.uv_layers.active.data
slot0_polys = [p for p in robot.data.polygons if p.material_index == 0]
slot1_polys = [p for p in robot.data.polygons if p.material_index == 1]
print(f"Slot 0 count: {len(slot0_polys)}, Slot 1 count: {len(slot1_polys)}")

# For Slot 1 (lights): print centers and normals and UVs
for pi, p in enumerate(slot1_polys[:10]):
    uvs = [uv_layer[li].uv for li in p.loop_indices]
    print(f"Slot 1 poly {pi}: center={p.center}, normal={p.normal}, UVs={[(round(u[0], 4), round(u[1], 4)) for u in uvs]}")

# Now, look at user image 2:
# What polygons in Slot 0 are right around the chest lights?
# Let's find the bounding box of Slot 1:
slot1_coords = [robot.data.vertices[vi].co for p in slot1_polys for vi in p.vertices]
s1_min_x, s1_max_x = min(c.x for c in slot1_coords), max(c.x for c in slot1_coords)
s1_min_y, s1_max_y = min(c.y for c in slot1_coords), max(c.y for c in slot1_coords)
s1_min_z, s1_max_z = min(c.z for c in slot1_coords), max(c.z for c in slot1_coords)
print(f"Slot 1 bounds: X=[{s1_min_x:.3f}, {s1_max_x:.3f}], Y=[{s1_min_y:.3f}, {s1_max_y:.3f}], Z=[{s1_min_z:.3f}, {s1_max_z:.3f}]")

# Check if any Slot 0 polygons have centers in Slot 1 bounds:
slot0_near = []
for p in slot0_polys:
    c = p.center
    if (s1_min_x <= c.x <= s1_max_x and
        s1_min_y - 0.2 <= c.y <= s1_max_y + 0.2 and
        s1_min_z - 0.2 <= c.z <= s1_max_z + 0.2):
        slot0_near.append(p)

print(f"Slot 0 polygons near Slot 1 bounds: {len(slot0_near)}")
for pi, p in enumerate(slot0_near[:10]):
    uvs = [uv_layer[li].uv for li in p.loop_indices]
    u_avg = sum(u[0] for u in uvs)/len(uvs)
    v_avg = sum(u[1] for u in uvs)/len(uvs)
    print(f"  Slot 0 near poly {pi}: center={p.center}, normal={p.normal}, uv=({u_avg:.3f}, {v_avg:.3f})")
