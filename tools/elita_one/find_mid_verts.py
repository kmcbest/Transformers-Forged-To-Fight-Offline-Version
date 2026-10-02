import bpy
from pathlib import Path

BLEND = Path(r"E:\Agent\TFTF-blender\tools\elita_one\elita_one_arcee_side_by_side.blend")

bpy.ops.wm.open_mainfile(filepath=str(BLEND))
scene = bpy.context.scene
scene.frame_set(11)
bpy.context.view_layer.update()

elita = bpy.data.objects.get("Elita_One_Mesh")
depsgraph = bpy.context.evaluated_depsgraph_get()
elita_eval = elita.evaluated_get(depsgraph)
mesh_eval = elita_eval.to_mesh()

# Search between Arcee and Elita: X in [-1.8, -0.2], Z in [4.0, 6.0]
mid_verts = []
for i, v in enumerate(mesh_eval.vertices):
    w_co = elita.matrix_world @ v.co
    if -1.8 < w_co.x < -0.2 and 4.0 < w_co.z < 6.0:
        mid_verts.append((i, w_co))

print(f"Found {len(mid_verts)} vertices in mid region.")
for idx, w_co in mid_verts[:15]:
    vgs = [(elita.vertex_groups[g.group].name, g.weight) for g in elita.data.vertices[idx].groups if g.weight > 0.01]
    print(f"Vert {idx}: World={w_co}, Rest={elita.data.vertices[idx].co}, VGs={vgs}")

elita_eval.to_mesh_clear()
