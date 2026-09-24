# -*- coding: utf-8 -*-
import sys
import bpy

sys.stdout.reconfigure(encoding='utf-8')

fbx_path = r"d:\Agent\tftf\3rd-party-models\transformers-fall-of-cybertron-demolishor\source\transformers fall of cybertron Demolishor.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path)

vh_mesh = bpy.data.objects.get("VH_Demolishor_SKEL.mo.dmx")
if vh_mesh:
    # Find vertices with maximum and minimum Y
    verts = [v.co for v in vh_mesh.data.vertices]
    max_y_v = max(verts, key=lambda v: v.y)
    min_y_v = min(verts, key=lambda v: v.y)
    print(f"Max Y vertex: {max_y_v}")
    print(f"Min Y vertex: {min_y_v}")
