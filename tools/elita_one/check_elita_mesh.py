import bpy

fbx_path = r"e:\Agent\TFTF-blender\3rd-party-models\transformers-galatic-trials-elita-one\source\Elita_One.fbx"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path)

mesh_obj = bpy.data.objects['SK_CH_11.001']
print(f"Mesh materials: {[m.name for m in mesh_obj.data.materials]}")
print(f"Vertex count: {len(mesh_obj.data.vertices)}")
print(f"Vertex groups: {len(mesh_obj.vertex_groups)}")

# Let's find vertices around the ankle (Z is lowest, or whichever axis is height)
# Let's inspect coordinate range
xs = [v.co.x for v in mesh_obj.data.vertices]
ys = [v.co.y for v in mesh_obj.data.vertices]
zs = [v.co.z for v in mesh_obj.data.vertices]
print(f"X: {min(xs):.2f} to {max(xs):.2f}")
print(f"Y: {min(ys):.2f} to {max(ys):.2f}")
print(f"Z: {min(zs):.2f} to {max(zs):.2f}")
