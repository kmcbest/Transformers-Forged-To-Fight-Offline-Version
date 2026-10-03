import bpy

fbx_path = r"e:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\ElitaOne\elita_one_prepared.fbx"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path)

mesh_obj = bpy.data.objects['cha_elita_one_gs_00']
print(f"Total vertex groups: {len(mesh_obj.vertex_groups)}")
print([vg.name for vg in mesh_obj.vertex_groups])
