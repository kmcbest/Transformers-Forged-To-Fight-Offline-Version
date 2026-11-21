import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

blend_path = r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\01_aligned_mesh\sideswipe_robot_aligned.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)

robot = bpy.data.objects.get("cha_sideswipe_main")

slot1_polys = [p for p in robot.data.polygons if p.material_index == 1]
print(f"Slot 1 (Mesh 20) total polys: {len(slot1_polys)}")

# Get left and right
left_polys = [p for p in slot1_polys if p.center.x < 0]
right_polys = [p for p in slot1_polys if p.center.x > 0]

print(f"Left: {len(left_polys)}, Right: {len(right_polys)}")

# Let's inspect the vertex coordinates of left_polys
left_verts = set(vi for p in left_polys for vi in p.vertices)
left_coords = [robot.data.vertices[vi].co for vi in left_verts]
print(f"Left verts count: {len(left_verts)}")
print(f"  X: [{min(c.x for c in left_coords):.3f}, {max(c.x for c in left_coords):.3f}]")
print(f"  Y: [{min(c.y for c in left_coords):.3f}, {max(c.y for c in left_coords):.3f}]")
print(f"  Z: [{min(c.z for c in left_coords):.3f}, {max(c.z for c in left_coords):.3f}]")

# Now let's inspect the pocket opening in Slot 0:
# Polygons in Slot 0 that form the trapezoid rim / frame:
rim_polys = []
uv_layer = robot.data.uv_layers.active.data
for p in robot.data.polygons:
    if p.material_index == 0:
        c = p.center
        if -1.6 <= c.x <= -0.5 and -1.3 <= c.y <= -1.0 and 9.4 <= c.z <= 10.1:
            rim_polys.append(p)

print(f"Slot 0 polygons in same bounding box: {len(rim_polys)}")
for p in rim_polys[:10]:
    uvs = [uv_layer[li].uv for li in p.loop_indices]
    u_avg = sum(u[0] for u in uvs)/len(uvs)
    v_avg = sum(u[1] for u in uvs)/len(uvs)
    print(f"  Rim poly {p.index}: center=({p.center.x:.3f}, {p.center.y:.3f}, {p.center.z:.3f}), uv=({u_avg:.3f}, {v_avg:.3f})")
