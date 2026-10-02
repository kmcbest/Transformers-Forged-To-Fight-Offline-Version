import bpy
import bmesh
import mathutils
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
BLEND_SBS = ROOT / "tools" / "demolishor" / "demolishor_ironhide_side_by_side.blend"

print("=== 1. Fixing Demolishor Shoulder/Back Pods in Blender ===")
bpy.ops.wm.open_mainfile(filepath=str(BLEND_SBS))
demo_mesh = bpy.data.objects.get("Demolishor_Mesh")
vg_spine1 = demo_mesh.vertex_groups.get("Spine1") or demo_mesh.vertex_groups.new(name="Spine1")

bm = bmesh.new()
bm.from_mesh(demo_mesh.data)
visited = set()
islands = []
for v in bm.verts:
    if v in visited: continue
    isl = []
    stack = [v]
    visited.add(v)
    while stack:
        cur = stack.pop()
        isl.append(cur)
        for e in cur.link_edges:
            other = e.other_vert(cur)
            if other not in visited:
                visited.add(other)
                stack.append(other)
    islands.append(isl)

# Any island with Z > 7.5 and center.y < 0.2 (behind or on top of shoulders/back) should be on Spine1
anchored = 0
for isl in islands:
    cos = np.array([demo_mesh.data.vertices[v.index].co for v in isl])
    center = cos.mean(axis=0)
    # Islands 451, 463, 471, 483: |X| > 2.0, Z > 7.5, max Z > 10.0m
    if abs(center[0]) > 2.0 and cos[:, 2].max() > 9.5:
        for v in isl:
            for g in demo_mesh.data.vertices[v.index].groups:
                demo_mesh.vertex_groups[g.group].remove([v.index])
            vg_spine1.add([v.index], 1.0, 'REPLACE')
            anchored += 1

print(f"[✓] Anchored {anchored} shoulder/back pod vertices rigidly to Spine1 (no more flying pods!).")

# Normalize weights & limit to 4 per vertex
bpy.context.view_layer.objects.active = demo_mesh
bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
bpy.ops.object.vertex_group_limit_total(group_select_mode='ALL', limit=4)
bpy.ops.object.vertex_group_normalize_all(group_select_mode='ALL', lock_active=False)
bpy.ops.object.mode_set(mode='OBJECT')

bm.free()
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_SBS))
print(f"[✓] Saved updated blend file to: {BLEND_SBS}")
