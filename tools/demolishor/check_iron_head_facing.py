# -*- coding: utf-8 -*-
import bpy
import sys

sys.stdout.reconfigure(encoding='utf-8')

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath="tools/demolishor/ironhide_extracted/ironhide.obj")
iron_obj = bpy.data.objects["ironhide"]

# Vertices around head (Y > 9.0)
head_verts = [v for v in iron_obj.data.vertices if v.co.y > 9.0]
print(f"Total head vertices: {len(head_verts)}")
zs = [v.co.z for v in head_verts]
print(f"Head Z range: [{min(zs):.3f}, {max(zs):.3f}]")

# Let's check highest Y vertex (top of head/shoulders)
top_v = max(iron_obj.data.vertices, key=lambda v: v.co.y)
print(f"Top vertex: ({top_v.co.x:.3f}, {top_v.co.y:.3f}, {top_v.co.z:.3f})")

# Check nose/face vs back of head in Ironhide
# In Ironhide bones:
# Head is at Z=0.09, Neck is at Z=0.06
# RightEye is at Z=0.62, LeftEye is at Z=0.62!
# Jaw is at Z=0.48!
print("Eyes and Jaw are at POSITIVE Z (+0.62, +0.48)!")
