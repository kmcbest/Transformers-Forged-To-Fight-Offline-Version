import os
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import bpy
import numpy as np

ROBOT_FBX = r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\01_source\Sideswipe.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=ROBOT_FBX)

scale = 89.73

meshes = [o for o in bpy.data.objects if o.type == 'MESH']
# Check vertex centers for each vertex group
vg_centers = {}
for m in meshes:
    vg_map = {vg.index: vg.name for vg in m.vertex_groups}
    for v in m.data.vertices:
        w_co = m.matrix_world @ v.co
        bx = w_co.x * scale
        by = -w_co.z * scale
        bz = w_co.y * scale
        for g in v.groups:
            if g.group in vg_map and g.weight > 0.5:
                vg_name = vg_map[g.group]
                if vg_name not in vg_centers:
                    vg_centers[vg_name] = []
                vg_centers[vg_name].append([bx, by, bz])

print("Sideswipe Mesh Vertex Group Centers in Blender space (scaled by 89.73):")
for name in sorted(vg_centers.keys()):
    arr = np.array(vg_centers[name])
    c = arr.mean(axis=0)
    print(f"  {name:20s} ({len(arr):4d} verts): center=({c[0]:6.3f}, {c[1]:6.3f}, {c[2]:6.3f}) bounds_Z=[{arr[:,2].min():6.3f}, {arr[:,2].max():6.3f}]")
