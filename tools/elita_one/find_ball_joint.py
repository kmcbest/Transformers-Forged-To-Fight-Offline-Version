import bpy

fbx_path = r"e:\Agent\TFTF-blender\3rd-party-models\transformers-galatic-trials-elita-one\source\Elita_One.fbx"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path)

mesh_obj = bpy.data.objects['SK_CH_11.001']

# Let's check vertices around the ankle ball joint:
# Left foot is around Y in [0.2, 0.9], X in [-0.1, 1.0], Z in [0.4, 0.9]
# Find which vertex groups cover vertices near the ball joint center
ball_verts = [v for v in mesh_obj.data.vertices if 0.4 < v.co.z < 0.8 and 0.4 < v.co.y < 0.7 and 0.2 < v.co.x < 0.6]
print(f"Total vertices in ball joint zone: {len(ball_verts)}")

vg_counts = {}
for v in ball_verts:
    for g in v.groups:
        vg_name = mesh_obj.vertex_groups[g.group].name
        vg_counts[vg_name] = vg_counts.get(vg_name, 0) + 1

for vg_name, cnt in sorted(vg_counts.items(), key=lambda x: x[1], reverse=True):
    print(f"  {vg_name}: {cnt}")
