import bpy
import bmesh
from pathlib import Path

BLEND = Path(r"E:\Agent\TFTF-blender\tools\elita_one\elita_one_arcee_side_by_side.blend")

bpy.ops.wm.open_mainfile(filepath=str(BLEND))
elita = bpy.data.objects.get("Elita_One_Mesh")

bm = bmesh.new()
bm.from_mesh(elita.data)
bm.verts.ensure_lookup_table()

# Island of vertex 486
v486 = bm.verts[486]
island = []
q = [v486]
visited = {486}
while q:
    cur = q.pop()
    island.append(cur.index)
    for e in cur.link_edges:
        other = e.other_vert(cur)
        if other.index not in visited:
            visited.add(other.index)
            q.append(other)

print(f"Island containing vert 486 has {len(island)} vertices.")

# Check all vertex groups and rest positions for this island
vgs_all = {}
rest_cos = [elita.data.vertices[i].co for i in island]
for i in island:
    for g in elita.data.vertices[i].groups:
        gname = elita.vertex_groups[g.group].name
        vgs_all[gname] = vgs_all.get(gname, 0) + g.weight

print(f"VGs in this island: {vgs_all}")
min_x = min(co.x for co in rest_cos)
max_x = max(co.x for co in rest_cos)
min_y = min(co.y for co in rest_cos)
max_y = max(co.y for co in rest_cos)
min_z = min(co.z for co in rest_cos)
max_z = max(co.z for co in rest_cos)
print(f"Rest bounds: X=[{min_x:.3f}, {max_x:.3f}], Y=[{min_y:.3f}, {max_y:.3f}], Z=[{min_z:.3f}, {max_z:.3f}]")

bm.free()
