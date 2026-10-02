import bpy
import mathutils

blend_path = r"E:\Agent\TFTF-blender\tools\elita_one\elita_one_arcee_side_by_side.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)

elita_mesh = bpy.data.objects.get("Elita_One_Mesh")
bpy.context.scene.frame_set(0)
bpy.context.view_layer.update()

depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj = elita_mesh.evaluated_get(depsgraph)
eval_mesh = eval_obj.to_mesh()

print("Scanning Elita One evaluated vertices for floating parts:")
floating_verts = []
for i, v in enumerate(eval_mesh.vertices):
    w_co = eval_obj.matrix_world @ v.co
    # Find verts where X > -1.0 (towards center or right) or Z > 8.8m
    if w_co.x > -1.0 or w_co.z > 8.8:
        floating_verts.append((i, w_co, elita_mesh.data.vertices[i].co))

print(f"Total floating vertices on Elita One: {len(floating_verts)}")
for i, w_co, rest_co in floating_verts[:15]:
    vgs = [(elita_mesh.vertex_groups[g.group].name, g.weight) for g in elita_mesh.data.vertices[i].groups]
    print(f"  Vert {i}: rest_co=({rest_co.x:.2f}, {rest_co.y:.2f}, {rest_co.z:.2f}) -> w_co=({w_co.x:.2f}, {w_co.y:.2f}, {w_co.z:.2f})")
    print(f"    vgroups: {vgs}")

eval_obj.to_mesh_clear()
