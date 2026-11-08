import bpy
import sys
import mathutils

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

bpy.ops.wm.read_factory_settings(use_empty=True)
obj_path = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Vortex\Grindor\cha_grindor_cin_rotf_00.obj"
print(f"Importing {obj_path}")
bpy.ops.import_scene.obj(filepath=obj_path)

obj = bpy.context.selected_objects[0] if bpy.context.selected_objects else bpy.data.objects[0]
bbox = [obj.matrix_world @ mathutils.Vector(c) for c in obj.bound_box]
xs = [c[0] for c in bbox]
ys = [c[1] for c in bbox]
zs = [c[2] for c in bbox]

print(f"Grindor 00 OBJ dimensions:")
print(f"  X span: [{min(xs):.2f}, {max(xs):.2f}] (width={max(xs)-min(xs):.2f})")
print(f"  Y span: [{min(ys):.2f}, {max(ys):.2f}] (depth={max(ys)-min(ys):.2f})")
print(f"  Z span: [{min(zs):.2f}, {max(zs):.2f}] (height={max(zs)-min(zs):.2f})")
print(f"  Total Vertices: {len(obj.data.vertices)}")
