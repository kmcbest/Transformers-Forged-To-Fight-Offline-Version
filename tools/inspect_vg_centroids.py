# -*- coding: utf-8 -*-
import sys
import json
import math
from pathlib import Path
import bpy
import mathutils

sys.stdout.reconfigure(encoding='utf-8')

# Run the alignment setup in Blender to inspect vertex coordinates vs bone coordinates
bpy.ops.wm.read_factory_settings(use_empty=True)

with open("tools/demolishor/ironhide_80_bones.json", "r", encoding="utf-8") as f:
    bones_data = json.load(f)

bones_dict = bones_data["bones"]

fbx_path = r"d:\Agent\tftf\3rd-party-models\transformers-fall-of-cybertron-demolishor\source\transformers fall of cybertron Demolishor.fbx"
bpy.ops.import_scene.fbx(filepath=fbx_path)

demolishor_mesh = bpy.data.objects.get("RB_DemolishorWeaponArm_SKEL.mo.dmx")

scale_factor = 1.775
demolishor_mesh.scale = (scale_factor, scale_factor, scale_factor)
bpy.context.view_layer.objects.active = demolishor_mesh
bpy.ops.object.transform_apply(scale=True)

demolishor_mesh.rotation_euler = (0, 0, math.radians(90))
bpy.ops.object.transform_apply(rotation=True)

min_z = min(v.co.z for v in demolishor_mesh.data.vertices)
demolishor_mesh.location.z -= min_z
bpy.ops.object.transform_apply(location=True)

# Check centroid of vertices in key vertex groups
for vg in demolishor_mesh.vertex_groups:
    if any(k in vg.name for k in ["Thigh", "Knee", "Shoulder", "Head", "Ankle", "Clav"]):
        verts = [v.co for v in demolishor_mesh.data.vertices for g in v.groups if g.group == vg.index]
        if verts:
            centroid = sum(verts, mathutils.Vector((0, 0, 0))) / len(verts)
            print(f"VG '{vg.name}': count={len(verts)}, centroid=({centroid.x:6.2f}, {centroid.y:6.2f}, {centroid.z:6.2f})")
