import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
import math

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=r"E:\Agent\RID_game\strongarm_extracted\strongarm_vehicle.obj")

car = bpy.data.objects['strongarm_vehicle']

# Step A: In raw OBJ, Front is -Z, Rear is +Z, Height is Y
# If we rotate 90 deg around X: Y -> Z (height).
# Z was length (-Z front). Rotated 90 deg around X: Z -> -Y. So Front (-Z) becomes +Y!
# Rear (+Z) becomes -Y!
car.rotation_euler = (1.5707963, 0, 0)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# Scale Z wheelbase (factor = 1.45168 on Y which is length now!)
# And scale width / height
car.scale = (1.0, 1.45168, 1.073)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

verts = car.data.vertices
print(f"Vehicle bounds in Blender:")
print(f"X (width):  [{min(v.co.x for v in verts):.3f}, {max(v.co.x for v in verts):.3f}]")
print(f"Y (length): [{min(v.co.y for v in verts):.3f}, {max(v.co.y for v in verts):.3f}]")
print(f"Z (height): [{min(v.co.z for v in verts):.3f}, {max(v.co.z for v in verts):.3f}]")
