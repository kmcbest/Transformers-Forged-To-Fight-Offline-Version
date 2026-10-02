import bpy

blend_path = r"E:\Agent\TFTF-blender\tools\elita_one\elita_one_arcee_setup.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)

mesh = bpy.data.objects.get("Elita_One_Mesh")
print(f"Elita_One_Mesh vertex groups ({len(mesh.vertex_groups)}):")
for vg in list(mesh.vertex_groups)[:15]:
    print(f"  {vg.name}")
print("  ...")
for vg in list(mesh.vertex_groups)[-15:]:
    print(f"  {vg.name}")
