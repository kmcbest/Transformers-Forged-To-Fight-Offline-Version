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

displacements = []
for i in range(len(elita.data.vertices)):
    p_rest = elita.data.vertices[i].co
    p_eval = mesh_eval.vertices[i].co
    dist = (p_eval - p_rest).length
    vgs = [(elita.vertex_groups[g.group].name, round(g.weight, 2)) for g in elita.data.vertices[i].groups if g.weight > 0.05]
    # filter out if only ForeArm
    vg_names = [name for name, _ in vgs]
    if not any("ForeArm" in name for name in vg_names):
        displacements.append((dist, i, p_rest, p_eval, vgs))

displacements.sort(key=lambda x: x[0], reverse=True)

print(f"Top 30 non-ForeArm vertex displacements in Frame 0:")
for dist, idx, rest, eval_p, vgs in displacements[:30]:
    print(f"Dist={dist:6.2f}m | Vert {idx:5d} | Rest=({rest.x:5.2f}, {rest.y:5.2f}, {rest.z:5.2f}) | Eval=({eval_p.x:5.2f}, {eval_p.y:5.2f}, {eval_p.z:5.2f}) | VGs={vgs}")

elita_eval.to_mesh_clear()
