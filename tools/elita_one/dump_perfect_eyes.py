import bpy
import json

bpy.ops.wm.read_factory_settings(use_empty=True)
fbx_path = r"E:\Agent\TFTF-blender\3rd-party-models\transformers-galatic-trials-elita-one\source\Elita_One.fbx"
bpy.ops.import_scene.fbx(filepath=fbx_path)

obj = bpy.data.objects['SK_CH_11.001']
mesh = obj.data
uv_layer = mesh.uv_layers.active

front_slits = [2386, 2387, 2392, 2393, 2398, 2400, 2409, 2413, 2414, 2423, 2427, 2431]
inner_socket = [3364, 3365, 3366, 3178, 3174, 3172]
perfect_eye_polys = front_slits + inner_socket

data = []
for idx in perfect_eye_polys:
    p = mesh.polygons[idx]
    side = "Left" if p.center.y > 0 else "Right"
    loop_uvs = [[uv_layer.data[l].uv.x, uv_layer.data[l].uv.y] for l in p.loop_indices]
    data.append({
        'index': p.index,
        'side': side,
        'center': [p.center.x, p.center.y, p.center.z],
        'uvs': loop_uvs
    })

with open(r"E:\Agent\TFTF-blender\tools\elita_one\perfect_eye_polys.json", "w") as f:
    json.dump(data, f)

print(f"Dumped {len(data)} perfect eye polys to JSON.")
bpy.ops.wm.quit_blender()
