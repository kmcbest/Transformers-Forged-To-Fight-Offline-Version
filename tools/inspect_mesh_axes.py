import bpy
import mathutils
from mathutils import Vector

obj_path = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\OptimusPrime\cha_optimusprime_gs_voyager2015_00.obj"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=obj_path)

obj = [o for o in bpy.context.scene.objects if o.type == 'MESH'][0]
mesh = obj.data

print(f"Mesh has {len(mesh.vertices)} vertices, {len(mesh.polygons)} polygons")
uv_layer = mesh.uv_layers.active.data

# Find bounding box
xs = [v.co.x for v in mesh.vertices]
ys = [v.co.y for v in mesh.vertices]
zs = [v.co.z for v in mesh.vertices]

print(f"X range: {min(xs):.2f} to {max(xs):.2f}")
print(f"Y range: {min(ys):.2f} to {max(ys):.2f}")
print(f"Z range: {min(zs):.2f} to {max(zs):.2f}")

# Categorize polygons by 3D position
# In Blender OBJ import: Z is typically up, or Y is up. Let's check which is up.
# Character is usually tall along one axis (min to max ~ 10-12 units)
height_axis = 'Y' if (max(ys) - min(ys)) > (max(zs) - min(zs)) else 'Z'
print(f"Height axis appears to be: {height_axis}")
