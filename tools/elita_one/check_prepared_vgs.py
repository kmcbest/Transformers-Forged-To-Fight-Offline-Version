import bpy

# Load elita_one_prepared.fbx
fbx_path = r"e:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\ElitaOne\elita_one_prepared.fbx"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path)

mesh_obj = None
for obj in bpy.data.objects:
    if obj.type == 'MESH':
        mesh_obj = obj
        break

print(f"Prepared mesh: {mesh_obj.name}, verts: {len(mesh_obj.data.vertices)}")
print("Vertex groups in prepared mesh:")
for vg in mesh_obj.vertex_groups:
    if any(k in vg.name.lower() for k in ['hip', 'thigh', 'calf', 'foot', 'toe', 'piston']):
        print(f"  {vg.name}")
