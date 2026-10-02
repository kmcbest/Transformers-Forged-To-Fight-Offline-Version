import bpy
import bmesh

fbx_path = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\ElitaOne\elita_one_prepared.fbx"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path)

mesh_obj = [o for o in bpy.context.scene.objects if o.type == 'MESH'][0]
bm = bmesh.new()
bm.from_mesh(mesh_obj.data)
bm.faces.ensure_lookup_table()

# Split into connected components (islands)
visited = set()
islands = []
for f in bm.faces:
    if f in visited:
        continue
    island = []
    queue = [f]
    visited.add(f)
    while queue:
        curr = queue.pop()
        island.append(curr)
        for e in curr.edges:
            for nbr in e.link_faces:
                if nbr not in visited:
                    visited.add(nbr)
                    queue.append(nbr)
    islands.append(island)

print(f"Total connected mesh islands: {len(islands)}")
# Check island volumes / orientation
inverted_islands = 0
for i, isl in enumerate(islands):
    # compute volume using divergence theorem
    vol = 0.0
    for f in isl:
        if len(f.verts) >= 3:
            v0 = f.verts[0].co
            for j in range(1, len(f.verts) - 1):
                v1 = f.verts[j].co
                v2 = f.verts[j + 1].co
                vol += v0.dot(v1.cross(v2)) / 6.0
    if vol < -1e-5:
        inverted_islands += 1
print(f"Closed islands with negative volume (inverted): {inverted_islands} / {len(islands)}")
