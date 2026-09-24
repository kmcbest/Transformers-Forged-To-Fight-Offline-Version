# -*- coding: utf-8 -*-
import bpy
import sys

sys.stdout.reconfigure(encoding='utf-8')

bpy.ops.wm.read_factory_settings(use_empty=True)

# Import Ironhide OBJ
bpy.ops.wm.obj_import(filepath="tools/demolishor/ironhide_extracted/ironhide.obj")
iron_obj = bpy.context.selected_objects[0] if bpy.context.selected_objects else bpy.data.objects[0]

print("Ironhide imported OBJ name:", iron_obj.name)
xs = [v.co.x for v in iron_obj.data.vertices]
ys = [v.co.y for v in iron_obj.data.vertices]
zs = [v.co.z for v in iron_obj.data.vertices]

print(f"Ironhide X range: [{min(xs):.3f}, {max(xs):.3f}] (size: {max(xs)-min(xs):.3f})")
print(f"Ironhide Y range: [{min(ys):.3f}, {max(ys):.3f}] (size: {max(ys)-min(ys):.3f})")
print(f"Ironhide Z range: [{min(zs):.3f}, {max(zs):.3f}] (size: {max(zs)-min(zs):.3f})")
