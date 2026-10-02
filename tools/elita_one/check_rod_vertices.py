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

# In Frame 11, looking at preview_elita_arcee_frame11_jab_strike.png:
# Those two sticks are pointing towards Arcee (to the viewer's left / -X)!
# World coordinates of Elita armature: (-2.6, 0, 0)
# Look at the yellow tips: X in [-3.5, -2.8], Y in [6.0, 7.5], Z in [4.5, 5.5]
rod_verts = []
for i, v in enumerate(mesh_eval.vertices):
    w_co = elita.matrix_world @ v.co
    if -3.5 < w_co.x < -2.7 and 6.0 < w_co.y < 7.5 and 4.8 < w_co.z < 5.6:
        rod_verts.append((i, w_co))

print(f"Found {len(rod_verts)} vertices in the yellow rods tip area in Frame 11.")
if rod_verts:
    for idx, w_co in rod_verts[:5]:
        vgs = [(elita.vertex_groups[g.group].name, g.weight) for g in elita.data.vertices[idx].groups if g.weight > 0.01]
        print(f"Vert {idx}: World={w_co}, Rest={elita.data.vertices[idx].co}, VGs={vgs}")

elita_eval.to_mesh_clear()
