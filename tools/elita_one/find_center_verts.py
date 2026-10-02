import bpy
import mathutils

blend_path = r"E:\Agent\TFTF-blender\tools\elita_one\elita_one_side_by_side.blend" if bpy.data.filepath else ""
bpy.ops.wm.open_mainfile(filepath=r"E:\Agent\TFTF-blender\tools\elita_one\elita_one_arcee_side_by_side.blend")

for m_obj in bpy.data.objects:
    if m_obj.type == 'MESH':
        print(f"\nChecking mesh: {m_obj.name}")
        center_verts = []
        for i, v in enumerate(m_obj.data.vertices):
            # world position with modifier evaluated
            depsgraph = bpy.context.evaluated_depsgraph_get()
            eval_obj = m_obj.evaluated_get(depsgraph)
            eval_mesh = eval_obj.to_mesh()
            w_co = eval_obj.matrix_world @ eval_mesh.vertices[i].co
            if abs(w_co.x) < 1.0: # near middle X=0
                center_verts.append((i, w_co))
            eval_obj.to_mesh_clear()
        print(f"  Mesh {m_obj.name} has {len(center_verts)} verts near center (X within 1m)")
        for i, co in center_verts[:5]:
            vgroups = [(m_obj.vertex_groups[g.group].name, g.weight) for g in m_obj.data.vertices[i].groups]
            print(f"    Vert {i} at {co}: {vgroups}")
