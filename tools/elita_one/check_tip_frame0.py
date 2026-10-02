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

# In Frame 0, the yellow tips are around World=(-2.3, 0.8, 5.0)
tips = []
for i, v in enumerate(mesh_eval.vertices):
    w = elita.matrix_world @ v.co
    if -2.5 < w.x < -2.1 and 0.7 < w.y < 1.3 and 4.8 < w.z < 5.3:
        tips.append(i)

print(f"Tip vertices in Frame 0: {len(tips)}")
for vi in tips[:5]:
    # Check original vertex group from raw FBX
    print(f"Vert {vi}: rest={elita.data.vertices[vi].co}, vgs={[(elita.vertex_groups[g.group].name, g.weight) for g in elita.data.vertices[vi].groups]}")

elita_eval.to_mesh_clear()
