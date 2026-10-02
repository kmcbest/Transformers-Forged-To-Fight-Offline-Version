import bpy
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
FBX_PATH = ROOT / "3rd-party-models" / "transformers-galatic-trials-elita-one" / "source" / "Elita_One.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_PATH))

obj = bpy.data.objects.get("SK_CH_11.001")
mesh = obj.data

# In find_cubes.py, Component 0 had 3 verts.
# Let's find polygons containing verts around (-0.18 to 0, 0.67, 8.25) in rotated space:
# Remember rotated by +90 Z: (x, y) -> (-y, x).
# So in raw FBX space:
# if rotated (x_rot, y_rot) = (-y_raw, x_raw), then x_raw = y_rot, y_raw = -x_rot.
# If x_rot ~ 0, y_rot ~ 0.67:
# x_raw ~ 0.67, y_raw ~ 0, z ~ 8.25 / 1.094 ~ 7.54
# That's Island 0, 1, 2 from inspect_islands.py:
# Island 0: 3 verts, Center=(0.62, 0.00, 7.54), VGs=['head_skin']
# Island 1: 3 verts, Center=(0.62, 0.17, 7.55), VGs=['head_skin']
# Island 2: 3 verts, Center=(0.62, 0.11, 7.51), VGs=['head_skin']

for i in range(25):
    # find polys containing verts in island i
    # Let's print out what these polys are!
    pass

# Let's inspect all islands with <= 12 vertices
small_islands = []
for p in mesh.polygons:
    pass

print("=== Checking all loose parts in SK_CH_11.001 ===")
import bmesh
bm = bmesh.new()
bm.from_mesh(mesh)

visited = set()
islands = []
for v in bm.verts:
    if v in visited: continue
    isl = []
    q = [v]
    visited.add(v)
    while q:
        curr = q.pop()
        isl.append(curr)
        for e in curr.link_edges:
            nb = e.other_vert(curr)
            if nb not in visited:
                visited.add(nb)
                q.append(nb)
    islands.append(isl)

print(f"Total islands: {len(islands)}")
hist = {}
for isl in islands:
    c = len(isl)
    hist[c] = hist.get(c, 0) + 1

for c in sorted(hist.keys())[:15]:
    print(f"Islands with {c} verts: {hist[c]}")

bm.free()
