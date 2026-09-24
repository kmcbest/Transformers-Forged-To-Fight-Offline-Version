# -*- coding: utf-8 -*-
import bpy
import sys

sys.stdout.reconfigure(encoding='utf-8')

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath="tools/demolishor/ironhide_extracted/ironhide.obj")
iron_obj = bpy.data.objects["ironhide"]

print("Ironhide bounding box after obj_import:")
for i, c in enumerate(iron_obj.bound_box):
    print(f"  corner {i}: ({c[0]:.2f}, {c[1]:.2f}, {c[2]:.2f})")
