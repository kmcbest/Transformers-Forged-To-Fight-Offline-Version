import bpy
from pathlib import Path

fbx_raw = r"E:\Agent\TFTF-blender\3rd-party-models\transformers-galatic-trials-elita-one\source\Elita_One.fbx"
fbx_prep = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\ElitaOne\elita_one_prepared.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_prep)

m = bpy.data.objects['cha_elita_one_gs_00']

# Check polygons by material index
p_slot0 = [p for p in m.data.polygons if p.material_index == 0]
p_slot1 = [p for p in m.data.polygons if p.material_index == 1]
print(f"Prepared mesh: Slot 0 has {len(p_slot0)} polys, Slot 1 has {len(p_slot1)} polys")

# Find polygons that make up the face (head front)
# Y is up in this mesh, Z is forward or backward?
# Let's inspect coordinates of head polygons
head_polys = []
for p in m.data.polygons:
    pts = [m.data.vertices[v].co for v in p.vertices]
    avg_y = sum(pt.y for pt in pts) / len(pts)
    if avg_y > 7.5: # head region
        head_polys.append((p, pts, avg_y))

print(f"Total head region polygons: {len(head_polys)}")
mat_counts = {}
for p, pts, y in head_polys:
    mat_counts[p.material_index] = mat_counts.get(p.material_index, 0) + 1
print(f"Head region material breakdown: {mat_counts}")
