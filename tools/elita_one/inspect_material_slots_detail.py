import bpy

fbx_path = r"E:\Agent\TFTF-blender\3rd-party-models\transformers-galatic-trials-elita-one\source\Elita_One.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path)

ch_mesh = bpy.data.objects['SK_CH_11.001']
print(f"Materials on {ch_mesh.name}:")
for i, m in enumerate(ch_mesh.data.materials):
    count = sum(1 for p in ch_mesh.data.polygons if p.material_index == i)
    print(f"  Slot {i}: {m.name} -> {count} polygons")

# Check bounds of polygons in each material slot to see what body parts they are!
for i, m in enumerate(ch_mesh.data.materials):
    polys = [p for p in ch_mesh.data.polygons if p.material_index == i]
    v_indices = set()
    for p in polys:
        v_indices.update(p.vertices)
    verts = [ch_mesh.data.vertices[v].co for v in v_indices]
    if verts:
        z_min = min(v.z for v in verts)
        z_max = max(v.z for v in verts)
        y_min = min(v.y for v in verts)
        y_max = max(v.y for v in verts)
        x_min = min(v.x for v in verts)
        x_max = max(v.x for v in verts)
        print(f"  Material {m.name} bbox: Z[{z_min:.2f}, {z_max:.2f}], Y[{y_min:.2f}, {y_max:.2f}], X[{x_min:.2f}, {x_max:.2f}]")
