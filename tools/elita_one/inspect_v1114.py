import bpy

blend_path = r"E:\Agent\TFTF-blender\tools\elita_one\elita_one_arcee_side_by_side.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)

arcee_mesh = bpy.data.objects.get("Arcee_Mesh")
v = arcee_mesh.data.vertices[1114]
print(f"Arcee Vert 1114 rest co: {v.co}")
print(f"Arcee Mesh loc: {arcee_mesh.location}, matrix_world trans: {arcee_mesh.matrix_world.translation}")
