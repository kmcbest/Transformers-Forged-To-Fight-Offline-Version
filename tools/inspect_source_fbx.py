# -*- coding: utf-8 -*-
import sys
from pathlib import Path
import bpy

sys.stdout.reconfigure(encoding='utf-8')

fbx_path = r"d:\Agent\tftf\3rd-party-models\transformers-fall-of-cybertron-demolishor\source\transformers fall of cybertron Demolishor.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path)

print(f"Total objects in source FBX: {len(bpy.data.objects)}")
for obj in bpy.data.objects:
    if obj.type == 'MESH':
        poly_count = len(obj.data.polygons)
        vert_count = len(obj.data.vertices)
        mats = [m.name for m in obj.data.materials if m]
        print(f"MESH: '{obj.name}' - {vert_count} verts, {poly_count} polys, materials: {mats}")
    elif obj.type == 'ARMATURE':
        print(f"ARMATURE: '{obj.name}' - {len(obj.data.bones)} bones")
    else:
        print(f"OTHER ({obj.type}): '{obj.name}'")
