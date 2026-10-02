import bpy

# Import raw FBX into clean scene to inspect vertex 7153
bpy.ops.wm.read_factory_settings(use_empty=True)
fbx_path = r"E:\Agent\TFTF-blender\3rd-party-models\transformers-galatic-trials-elita-one\source\Elita_One.fbx"
bpy.ops.import_scene.fbx(filepath=fbx_path)

mesh = bpy.data.objects.get("SK_CH_11.001")
for v_idx in [7153, 7255, 7260, 8140]:
    v = mesh.data.vertices[v_idx]
    vgs = [(mesh.vertex_groups[g.group].name, g.weight) for g in v.groups]
    print(f"Raw FBX vert {v_idx} at {v.co}: {vgs}")
