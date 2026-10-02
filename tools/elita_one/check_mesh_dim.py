import bpy

fbx_prep = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\ElitaOne\elita_one_prepared.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_prep)

m = bpy.data.objects['cha_elita_one_gs_00']
print("Mesh dimensions:", m.dimensions)

# Check materials and texture assignments
for mat in m.data.materials:
    print("Material:", mat.name)
