import bpy

fbx_raw = r"E:\Agent\TFTF-blender\3rd-party-models\transformers-galatic-trials-elita-one\source\Elita_One.fbx"
fbx_prep = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\ElitaOne\elita_one_prepared.fbx"

# 1. Check raw FBX
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_raw)
m_raw = bpy.data.objects['SK_CH_11.001']
print(f"Raw FBX: {len(m_raw.data.vertices)} vertices, {len(m_raw.data.polygons)} polygons")
print(f"Raw Materials: {[m.name for m in m_raw.data.materials]}")
for i, m in enumerate(m_raw.data.materials):
    p_cnt = sum(1 for p in m_raw.data.polygons if p.material_index == i)
    print(f"  Slot {i} ({m.name}): {p_cnt} polys")

# 2. Check prepared FBX
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_prep)
m_prep = None
for o in bpy.data.objects:
    if o.type == 'MESH':
        m_prep = o
        break

print(f"\nPrepared FBX: {len(m_prep.data.vertices)} vertices, {len(m_prep.data.polygons)} polygons")
print(f"Prepared Materials: {[m.name for m in m_prep.data.materials]}")
for i, m in enumerate(m_prep.data.materials):
    p_cnt = sum(1 for p in m_prep.data.polygons if p.material_index == i)
    print(f"  Slot {i} ({m.name}): {p_cnt} polys")
