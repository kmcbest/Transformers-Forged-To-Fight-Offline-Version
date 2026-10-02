import bpy
import mathutils

blend_path = r"E:\Agent\TFTF-blender\tools\elita_one\elita_one_arcee_side_by_side.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)

bpy.context.scene.frame_set(0)
bpy.context.view_layer.update()

for o in bpy.data.objects:
    if o.type == 'MESH':
        depsgraph = bpy.context.evaluated_depsgraph_get()
        eval_obj = o.evaluated_get(depsgraph)
        eval_mesh = eval_obj.to_mesh()
        # Find any polygon or vertex near X=0, Z=7..10
        high_verts = []
        for i, v in enumerate(eval_mesh.vertices):
            w = eval_obj.matrix_world @ v.co
            if w.z > 7.0 and abs(w.x) < 1.5:
                high_verts.append((i, w, o.data.vertices[i].co))
        print(f"Object {o.name}: {len(high_verts)} vertices high near center (Z>7, |X|<1.5)")
        if high_verts:
            for i, w, r in high_verts[:5]:
                vgs = [(o.vertex_groups[g.group].name, g.weight) for g in o.data.vertices[i].groups]
                print(f"  vert {i}: rest=({r.x:.2f},{r.y:.2f},{r.z:.2f}) -> world=({w.x:.2f},{w.y:.2f},{w.z:.2f}), vgs={vgs}")
        eval_obj.to_mesh_clear()
