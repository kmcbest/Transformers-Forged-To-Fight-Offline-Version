import bpy
import bmesh
import mathutils
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
BLEND = ROOT / "tools" / "elita_one" / "elita_one_arcee_side_by_side.blend"

bpy.ops.wm.open_mainfile(filepath=str(BLEND))
scene = bpy.context.scene
scene.frame_set(0)
bpy.context.view_layer.update()

elita = bpy.data.objects.get("Elita_One_Mesh")
mesh = elita.data

# We want to find connected components (islands) of vertices in elita mesh
# and see which island has world coordinates near the top right of Elita:
# Elita armature is at (-2.6, 0, 0).
# In frame 0, looking at preview_elita_arcee_frame00_guard.png:
# Outliers are at top left of Elita's head (in camera view):
# Camera is at (0, 18.5, 4.4) facing -Y.
# In world coordinates:
# Viewer Left = +X (Arcee side)
# Viewer Right = -X (Elita side)
# Viewer Top = +Z
# So top left of Elita in viewer space:
# Elita center is X = -2.6.
# To the left of Elita (towards Arcee / towards +X): X is between -2.5 and -1.0!
# And Z is high: Z between 6.0 and 8.0!
# Let's inspect evaluated vertices with X > -2.2 and Z > 6.0!

depsgraph = bpy.context.evaluated_depsgraph_get()
elita_eval = elita.evaluated_get(depsgraph)
mesh_eval = elita_eval.to_mesh()

print("Searching for vertices in the 'cubes' region (X between -2.2 and -1.0, Z > 6.0)...")
suspect_indices = set()
for i, v in enumerate(mesh_eval.vertices):
    w_co = elita.matrix_world @ v.co
    if -2.3 < w_co.x < -0.8 and w_co.z > 6.0:
        suspect_indices.add(i)

print(f"Found {len(suspect_indices)} suspect vertices in this region.")

# Group these vertices into connected components in the base mesh
bm = bmesh.new()
bm.from_mesh(mesh)
bm.verts.ensure_lookup_table()

visited = set()
cube_islands = []
for idx in suspect_indices:
    if idx in visited:
        continue
    v = bm.verts[idx]
    island = []
    q = [v]
    visited.add(idx)
    while q:
        curr = q.pop()
        island.append(curr.index)
        for e in curr.link_edges:
            nb = e.other_vert(curr)
            if nb.index not in visited:
                visited.add(nb.index)
                q.append(nb)
    cube_islands.append(island)

print(f"Number of connected components containing suspect vertices: {len(cube_islands)}")
for idx, isl in enumerate(cube_islands[:10]):
    # Get original coords
    orig_cos = [mesh.vertices[vi].co for vi in isl]
    avg_co = sum(orig_cos, mathutils.Vector()) / len(orig_cos)
    # Check vertex groups
    vgs = {}
    for vi in isl:
        for g in mesh.vertices[vi].groups:
            gname = elita.vertex_groups[g.group].name
            vgs[gname] = vgs.get(gname, 0) + g.weight
    print(f"Component {idx}: {len(isl)} verts, Original Center={avg_co}, Groups={vgs}")

bm.free()
elita_eval.to_mesh_clear()
