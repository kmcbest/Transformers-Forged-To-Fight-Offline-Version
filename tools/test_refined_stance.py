# -*- coding: utf-8 -*-
import sys
import json
import math
from pathlib import Path
import bpy
import mathutils

sys.stdout.reconfigure(encoding='utf-8')

bpy.ops.wm.read_factory_settings(use_empty=True)

fbx_path = r"d:\Agent\tftf\3rd-party-models\transformers-fall-of-cybertron-demolishor\source\transformers fall of cybertron Demolishor.fbx"
bpy.ops.import_scene.fbx(filepath=fbx_path)

mesh = bpy.data.objects.get("RB_DemolishorWeaponArm_SKEL.mo.dmx")

# Scale by 1.85
scale_factor = 1.85
mesh.scale = (scale_factor, scale_factor, scale_factor)
bpy.context.view_layer.objects.active = mesh
bpy.ops.object.transform_apply(scale=True)

mesh.rotation_euler = (0, 0, math.radians(90))
bpy.ops.object.transform_apply(rotation=True)

min_z = min(v.co.z for v in mesh.data.vertices)
# Shift up so feet sit on ground but hips/shoulders match Ironhide
mesh.location.z -= (min_z - 0.45)
bpy.ops.object.transform_apply(location=True)

# Apply 18% leg stance narrowing for Z < 4.5
for v in mesh.data.vertices:
    if v.co.z < 4.5:
        # Smooth falloff between Z=1.0 and Z=4.5
        t = max(0.0, min(1.0, (4.5 - v.co.z) / 3.5))
        factor = 1.0 - 0.20 * t
        v.co.x *= factor

# Check new centroids
for vg in mesh.vertex_groups:
    if any(k in vg.name for k in ["Thigh", "Knee", "Shoulder", "Head", "Ankle"]):
        verts = [v.co for v in mesh.data.vertices for g in v.groups if g.group == vg.index]
        if verts:
            centroid = sum(verts, mathutils.Vector((0, 0, 0))) / len(verts)
            print(f"VG '{vg.name:22s}': centroid=({centroid.x:6.2f}, {centroid.y:6.2f}, {centroid.z:6.2f})")
