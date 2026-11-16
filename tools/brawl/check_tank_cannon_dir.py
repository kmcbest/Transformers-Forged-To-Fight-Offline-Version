import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

fbx_path = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Brawl\brawl_tank.fbx"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path)

for o in bpy.data.objects:
    if o.type == 'MESH':
        tank = o
        break

# The cannon is the highest or forward-most feature
# Let's find vertices with highest Y (turret/cannon)
high_y_verts = [v for v in tank.data.vertices if v.co.y > 2.5]
# Let's see the Z range of high Y verts
zs = [v.co.z for v in high_y_verts]
print(f"High Y (turret/cannon) Z range: [{min(zs):.3f}, {max(zs):.3f}]")

# Let's find vertex with max Z and min Z:
max_z_v = max(tank.data.vertices, key=lambda v: v.co.z)
min_z_v = min(tank.data.vertices, key=lambda v: v.co.z)
print(f"Max Z vertex: co=({max_z_v.co.x:.3f}, {max_z_v.co.y:.3f}, {max_z_v.co.z:.3f})")
print(f"Min Z vertex: co=({min_z_v.co.x:.3f}, {min_z_v.co.y:.3f}, {min_z_v.co.z:.3f})")
