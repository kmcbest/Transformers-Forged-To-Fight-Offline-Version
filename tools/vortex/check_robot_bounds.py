import bpy
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import mathutils

ROBOT_BLEND = r"E:\Agent\TFTF-blender\3rd-party-models\vortex\robot\vortex_robot.blend"
bpy.ops.wm.open_mainfile(filepath=ROBOT_BLEND)

# Calculate combined bounding box of all meshes in scene
all_coords = []
for obj in bpy.data.objects:
    if obj.type == 'MESH':
        for corner in obj.bound_box:
            world_corner = obj.matrix_world @ mathutils.Vector(corner)
            all_coords.append(world_corner)

xs = [c[0] for c in all_coords]
ys = [c[1] for c in all_coords]
zs = [c[2] for c in all_coords]

min_x, max_x = min(xs), max(xs)
min_y, max_y = min(ys), max(ys)
min_z, max_z = min(zs), max(zs)

center_x = (min_x + max_x) / 2.0
center_y = (min_y + max_y) / 2.0
center_z = (min_z + max_z) / 2.0
height = max_z - min_z
width = max_x - min_x
depth = max_y - min_y

print(f"Robot Bounding Box:")
print(f"  X (width): [{min_x:.2f}, {max_x:.2f}] span={width:.2f}")
print(f"  Y (depth): [{min_y:.2f}, {max_y:.2f}] span={depth:.2f}")
print(f"  Z (height): [{min_z:.2f}, {max_z:.2f}] span={height:.2f}")
print(f"  Center: ({center_x:.2f}, {center_y:.2f}, {center_z:.2f})")

# Check bone orientation (e.g. head, spine, feet)
arm = bpy.data.objects.get("Vortex_ARM")
if arm:
    head_b = arm.data.bones.get("bip_head")
    if head_b:
        print(f"Head bone head: {head_b.head}, tail: {head_b.tail}")
