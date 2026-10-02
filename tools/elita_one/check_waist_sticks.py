import bpy
from pathlib import Path

BLEND = Path(r"E:\Agent\TFTF-blender\tools\elita_one\elita_one_arcee_side_by_side.blend")

bpy.ops.wm.open_mainfile(filepath=str(BLEND))
scene = bpy.context.scene
scene.frame_set(0)
bpy.context.view_layer.update()

elita = bpy.data.objects.get("Elita_One_Mesh")
depsgraph = bpy.context.evaluated_depsgraph_get()
elita_eval = elita.evaluated_get(depsgraph)
mesh_eval = elita_eval.to_mesh()

# In Frame 0, looking at preview_elita_arcee_frame00_guard.png:
# Near Elita's waist: Z in [4.5, 5.5], Y in [-0.5, 1.0], X in [-3.0, -2.0]
# Let's find vertices with Y > 0.5 near waist Z in [4.5, 5.5]
suspects = []
for i, v in enumerate(mesh_eval.vertices):
    w_co = elita.matrix_world @ v.co
    # Elita is at X = -2.6. In front of her body is +Y.
    # The sticks poke forward around Y in [0.8, 1.5] and Z in [4.5, 5.5]
    if -3.5 < w_co.x < -1.5 and 0.6 < w_co.y < 1.8 and 4.5 < w_co.z < 5.8:
        suspects.append(i)

print(f"Found {len(suspects)} vertices in front of waist.")
# Find their vertex groups and rest positions
from collections import Counter
vg_cnt = Counter()
for vi in suspects:
    for g in elita.data.vertices[vi].groups:
        gname = elita.vertex_groups[g.group].name
        if g.weight > 0.1:
            vg_cnt[gname] += 1

print("Vertex Groups of waist sticks:")
for name, c in vg_cnt.most_common(10):
    print(f"  {name}: {c}")

elita_eval.to_mesh_clear()
