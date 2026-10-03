import bpy
import bmesh

fbx_path = r"e:\Agent\TFTF-blender\3rd-party-models\transformers-galatic-trials-elita-one\source\Elita_One.fbx"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path)

mesh_obj = bpy.data.objects['SK_CH_11.001']
bm = bmesh.new()
bm.from_mesh(mesh_obj.data)

# Find connected components (islands)
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
        for edge in curr.link_edges:
            other = edge.other_vert(curr)
            if other not in visited:
                visited.add(other)
                queue.append(other)
    islands.append(island)

print(f"Total islands in SK_CH_11.001: {len(islands)}")
# Sort islands by vertex count descending
islands.sort(key=lambda isl: len(isl), reverse=True)
for i, isl in enumerate(islands[:25]):
    xs = [v.co.x for v in isl]
    ys = [v.co.y for v in isl]
    zs = [v.co.z for v in isl]
    center = (sum(xs)/len(xs), sum(ys)/len(ys), sum(zs)/len(zs))
    dims = (max(xs)-min(xs), max(ys)-min(ys), max(zs)-min(zs))
    print(f"Island {i}: verts={len(isl)}, center=({center[0]:.2f}, {center[1]:.2f}, {center[2]:.2f}), dims=({dims[0]:.2f}, {dims[1]:.2f}, {dims[2]:.2f})")
