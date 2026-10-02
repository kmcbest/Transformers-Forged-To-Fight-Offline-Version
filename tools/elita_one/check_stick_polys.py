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

# Search for the exact vertices of the yellow sticks:
# In Frame 11, the tip is around X in [-3.5, -3.3], Y in [6.4, 6.7], Z in [5.1, 5.5]
stick_verts = []
for i, v in enumerate(mesh_eval.vertices):
    w_co = elita.matrix_world @ v.co
    if -3.55 < w_co.x < -3.35 and 6.3 < w_co.y < 6.8 and 5.0 < w_co.z < 5.6:
        stick_verts.append(i)

print(f"Stick vertices ({len(stick_verts)}): {stick_verts[:20]}")

# Find all polygons using any of these stick vertices
stick_polys = []
for p in elita.data.polygons:
    if any(vi in stick_verts for vi in p.vertices):
        stick_polys.append(p)

print(f"Stick polys ({len(stick_polys)}):")
for p in stick_polys[:10]:
    v_indices = list(p.vertices)
    vgs = [list(elita.data.vertices[vi].groups) for vi in v_indices]
    vg_names = [[elita.vertex_groups[g.group].name for g in g_list] for g_list in vgs]
    print(f"  Poly {p.index}: verts={v_indices}, vgs={vg_names}")

elita_eval.to_mesh_clear()
