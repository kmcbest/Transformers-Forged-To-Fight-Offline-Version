# -*- coding: utf-8 -*-
import bpy
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
fbx_path = ROOT / "toolchain" / "unity_build_project" / "Assets" / "Demolishor" / "demolishor_prepared.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(fbx_path))

print(f"=== Objects in {fbx_path.name} ===")
for obj in bpy.data.objects:
    print(f"  Name: {obj.name:30s} | Type: {obj.type}")
    if obj.type == 'MESH':
        print(f"    Vertices: {len(obj.data.vertices)}")
        print(f"    Vertex Groups: {len(obj.vertex_groups)}")
        print(f"    Sample VGs: {[vg.name for vg in obj.vertex_groups[:10]]}")
    elif obj.type == 'ARMATURE':
        print(f"    Bones: {len(obj.data.bones)}")
