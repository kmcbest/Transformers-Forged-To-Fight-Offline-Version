import bpy

fbx_raw = r"E:\Agent\TFTF-blender\3rd-party-models\transformers-galatic-trials-elita-one\source\Elita_One.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_raw)
m = bpy.data.objects['SK_CH_11.001']
print("Raw FBX dimensions:", m.dimensions)
head_pts = [v.co for v in m.data.vertices if v.co.z > 6.0]
print(f"Verts with Z > 6.0: {len(head_pts)}")
if head_pts:
    print(f"Z range: [{min(v.z for v in head_pts):.2f}, {max(v.z for v in head_pts):.2f}]")
    print(f"Y range: [{min(v.y for v in head_pts):.2f}, {max(v.y for v in head_pts):.2f}]")
    print(f"X range: [{min(v.x for v in head_pts):.2f}, {max(v.x for v in head_pts):.2f}]")
