# -*- coding: utf-8 -*-
import sys
from pathlib import Path
import bpy
import mathutils

sys.stdout.reconfigure(encoding='utf-8')

fbx_path = r"d:\Agent\tftf\3rd-party-models\transformers-fall-of-cybertron-demolishor\source\transformers fall of cybertron Demolishor.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path)

vh_mesh = bpy.data.objects.get("VH_Demolishor_SKEL.mo.dmx")
if vh_mesh:
    bbox = [vh_mesh.matrix_world @ mathutils.Vector(corner) for corner in vh_mesh.bound_box]
    xs = [v.x for v in bbox]
    ys = [v.y for v in bbox]
    zs = [v.z for v in bbox]
    print("=== VH_Demolishor_SKEL Dimensions in Source FBX ===")
    print(f"  X (range): [{min(xs):.2f}, {max(xs):.2f}], size: {max(xs)-min(xs):.2f}")
    print(f"  Y (range): [{min(ys):.2f}, {max(ys):.2f}], size: {max(ys)-min(ys):.2f}")
    print(f"  Z (range): [{min(zs):.2f}, {max(zs):.2f}], size: {max(zs)-min(zs):.2f}")
    print(f"  Vertex count: {len(vh_mesh.data.vertices)}")
    print(f"  Vertex groups count: {len(vh_mesh.vertex_groups)}")
    vgs = [vg.name for vg in vh_mesh.vertex_groups]
    print(f"  Sample VGs (first 20): {vgs[:20]}")
