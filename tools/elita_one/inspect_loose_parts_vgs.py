import bpy

blend_path = r"E:\Agent\TFTF-blender\tools\elita_one\elita_one_arcee_setup.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)

elita_mesh = bpy.data.objects.get("Elita_One_Mesh")
print("Vertex 7153 groups:", [(elita_mesh.vertex_groups[g.group].name, g.weight) for g in elita_mesh.data.vertices[7153].groups])
print("Vertex 7255 groups:", [(elita_mesh.vertex_groups[g.group].name, g.weight) for g in elita_mesh.data.vertices[7255].groups])

# Check a few loose parts
bpy.ops.object.select_all(action='DESELECT')
elita_mesh.select_set(True)
bpy.context.view_layer.objects.active = elita_mesh
bpy.ops.mesh.separate(type='LOOSE')
parts = [p for p in bpy.context.selected_objects if p.type == 'MESH']
print(f"Total parts: {len(parts)}")
for p in parts[:10]:
    v = p.data.vertices[0]
    # find group names
    vgs = [(p.vertex_groups[g.group].name, g.weight) for g in v.groups]
    print(f"Part with {len(p.data.vertices)} verts at {p.location}: {vgs}")
