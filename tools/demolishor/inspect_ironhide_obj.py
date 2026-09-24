import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath="tools/demolishor/ironhide_extracted/ironhide.obj")

obj = bpy.context.selected_objects[0]
print(f"Imported {obj.name}: vertices={len(obj.data.vertices)}")
verts = [v.co for v in obj.data.vertices]
xs = [v.x for v in verts]
ys = [v.y for v in verts]
zs = [v.z for v in verts]
print(f"X: {min(xs):.2f} to {max(xs):.2f}")
print(f"Y: {min(ys):.2f} to {max(ys):.2f}")
print(f"Z: {min(zs):.2f} to {max(zs):.2f}")
