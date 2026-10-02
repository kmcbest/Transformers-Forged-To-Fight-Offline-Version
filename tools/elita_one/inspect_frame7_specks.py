import bpy
from pathlib import Path

BLEND = Path(r"E:\Agent\TFTF-blender\tools\elita_one\elita_one_arcee_side_by_side.blend")

bpy.ops.wm.open_mainfile(filepath=str(BLEND))
scene = bpy.context.scene
scene.frame_set(7)
bpy.context.view_layer.update()

# Check all objects in scene
print("=== All Objects in Scene ===")
for obj in bpy.data.objects:
    print(f"Object: {obj.name}, Type: {obj.type}, Parent: {obj.parent.name if obj.parent else None}")

elita = bpy.data.objects.get("Elita_One_Mesh")
arcee = bpy.data.objects.get("Arcee_Mesh")

depsgraph = bpy.context.evaluated_depsgraph_get()
elita_eval = elita.evaluated_get(depsgraph)
mesh_eval = elita_eval.to_mesh()

print(f"\nTotal vertices in Elita_One_Mesh: {len(mesh_eval.vertices)}")
print(f"Total polygons: {len(mesh_eval.polygons)}")
print(f"Total edges: {len(mesh_eval.edges)}")

# Check for loose vertices (vertices not in any polygon)
poly_verts = set()
for p in mesh_eval.polygons:
    for v in p.vertices:
        poly_verts.add(v)

loose_verts = [i for i in range(len(mesh_eval.vertices)) if i not in poly_verts]
print(f"Loose vertices (not in any poly): {len(loose_verts)}")

# Check for tiny / degenerate faces or very small disconnected components
import bmesh
bm = bmesh.new()
bm.from_mesh(elita.data)

visited = set()
islands = []
for v in bm.verts:
    if v in visited: continue
    isl = []
    q = [v]
    visited.add(v)
    while q:
        curr = q.pop()
        isl.append(curr.index)
        for e in curr.link_edges:
            nb = e.other_vert(curr)
            if nb not in visited:
                visited.add(nb)
                q.append(nb)
    islands.append(isl)

print(f"Total connected components (islands): {len(islands)}")
small_islands = [isl for isl in islands if len(isl) <= 4]
print(f"Small islands (<= 4 vertices): {len(small_islands)}")

# In Frame 7, find vertices in the top-right box:
# Camera or viewport perspective.
# Let's find vertices in world space with evaluated coordinates far from the body:
world_coords = [elita.matrix_world @ v.co for v in mesh_eval.vertices]
outliers = []
for i, wc in enumerate(world_coords):
    # Elita center is around (-2.6, 1.0, 4.0)
    # Any vertex with Z > 8.0 or X < -4.5 or X > 0.0 or Y > 5.0 or Y < -3.0
    if wc.z > 8.2 or wc.x > -0.5 or wc.x < -5.0 or wc.y > 6.0 or wc.y < -3.0:
        outliers.append((i, wc, elita.data.vertices[i].co))

print(f"Outlier vertices in Frame 7: {len(outliers)}")
for i, wc, orig_co in outliers[:15]:
    vgs = [(elita.vertex_groups[g.group].name, g.weight) for g in elita.data.vertices[i].groups if g.weight > 0.01]
    print(f"Vert {i}: World={wc}, Rest={orig_co}, VGs={vgs}")

bm.free()
elita_eval.to_mesh_clear()
