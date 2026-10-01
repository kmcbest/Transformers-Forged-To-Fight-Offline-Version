# -*- coding: utf-8 -*-
import bpy
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
BLEND_PATH = ROOT / "tools" / "demolishor" / "demolishor_phase2_inspect.blend"

bpy.ops.wm.open_mainfile(filepath=str(BLEND_PATH))

mesh = bpy.data.objects.get("cha_demolishor_gs_01")
arm = bpy.data.objects.get("Ironhide_Reference_Armature")

print("=== Demolishor Vertex Groups on Final Mesh ===")
for vg in mesh.vertex_groups:
    verts = [v for v in mesh.data.vertices if any(g.group == vg.index and g.weight > 0.5 for g in v.groups)]
    if verts:
        zs = [v.co.z for v in verts]
        xs = [v.co.x for v in verts]
        print(f"  {vg.name:18s}: {len(verts):4d} verts | Z: [{min(zs):.2f}, {max(zs):.2f}] | X: [{min(xs):.2f}, {max(xs):.2f}]")
