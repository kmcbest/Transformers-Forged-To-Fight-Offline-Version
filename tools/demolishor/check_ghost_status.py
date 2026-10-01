# -*- coding: utf-8 -*-
import bpy

print("=== Scene Objects ===")
for obj in bpy.data.objects:
    print(f"Name: {obj.name:30s} | Type: {obj.type:10s} | Hide_viewport: {obj.hide_viewport} | Hide_get: {obj.hide_get()} | Display_type: {obj.display_type}")

ghost = bpy.data.objects.get("Ironhide_Ghost_Reference")
if ghost:
    print("\nGhost details:")
    print(f"  verts: {len(ghost.data.vertices)}")
    print(f"  materials: {[m.name for m in ghost.data.materials if m]}")
    print(f"  display_type: {ghost.display_type}")
