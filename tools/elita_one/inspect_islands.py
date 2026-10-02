import bpy
import bmesh
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
FBX_PATH = ROOT / "3rd-party-models" / "transformers-galatic-trials-elita-one" / "source" / "Elita_One.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_PATH))

obj = bpy.data.objects.get("SK_CH_11.001")
mesh = obj.data

bm = bmesh.new()
bm.from_mesh(mesh)

# Find connected components / islands
visited = set()
islands = []

for v in bm.verts:
    if v in visited:
        continue
    island = []
    queue = [v]
    visited.add(v)
    while queue:
        curr = queue.pop()
        island.append(curr)
        for e in curr.link_edges:
            other = e.other_vert(curr)
            if other not in visited:
                visited.add(other)
                queue.append(other)
    islands.append(island)

print(f"Total connected components / islands in SK_CH_11.001: {len(islands)}")
# Sort islands by vertex count
islands.sort(key=lambda isl: len(isl))

dvert_lay = bm.verts.layers.deform.active

for i, isl in enumerate(islands[:25]): # inspect small islands
    centers = [v.co for v in isl]
    avg_x = sum(c.x for c in centers) / len(centers)
    avg_y = sum(c.y for c in centers) / len(centers)
    avg_z = sum(c.z for c in centers) / len(centers)
    
    # Check vertex groups for this island
    vg_names = set()
    for v in isl:
        dvert = v[dvert_lay]
        for g_idx in dvert.keys():
            vg_names.add(obj.vertex_groups[g_idx].name)
            
    print(f"Island {i}: {len(isl)} verts, Center=({avg_x:.2f}, {avg_y:.2f}, {avg_z:.2f}), VGs={list(vg_names)[:5]}")

bm.free()
