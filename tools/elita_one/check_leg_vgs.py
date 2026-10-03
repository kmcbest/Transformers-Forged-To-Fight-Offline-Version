import bpy

# Load Elita_One.fbx
fbx_path = r"e:\Agent\TFTF-blender\3rd-party-models\transformers-galatic-trials-elita-one\source\Elita_One.fbx"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path)

mesh_obj = bpy.data.objects['SK_CH_11.001']

# Let's inspect vertex groups for ankle/foot
print("Vertex groups containing foot/ankle/leg:")
leg_vgs = [vg.name for vg in mesh_obj.vertex_groups if any(k in vg.name.lower() for k in ['foot', 'ankle', 'calf', 'leg', 'toe', 'heel'])]
print(leg_vgs)

# Let's find vertices with weights to foot/calf/ankle and see what geometry they form
for vg_name in leg_vgs:
    vg = mesh_obj.vertex_groups[vg_name]
    verts_in_vg = [v for v in mesh_obj.data.vertices if any(g.group == vg.index and g.weight > 0.1 for g in v.groups)]
    if verts_in_vg:
        zs = [v.co.z for v in verts_in_vg]
        print(f"  VG '{vg_name}': {len(verts_in_vg)} verts, Z min={min(zs):.2f}, max={max(zs):.2f}")
