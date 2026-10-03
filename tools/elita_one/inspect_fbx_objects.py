import bpy

# Check meshes in Elita_One.fbx
fbx_path = r"e:\Agent\TFTF-blender\3rd-party-models\transformers-galatic-trials-elita-one\source\Elita_One.fbx"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path)

print("=== FBX Objects ===")
for obj in bpy.data.objects:
    print(f"Name: {obj.name}, type: {obj.type}, parent: {obj.parent.name if obj.parent else None}")
    if obj.type == 'MESH':
        print(f"  verts: {len(obj.data.vertices)}, bounds: {obj.dimensions}")
