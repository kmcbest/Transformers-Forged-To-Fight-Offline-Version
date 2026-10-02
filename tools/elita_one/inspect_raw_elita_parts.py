import bpy
from pathlib import Path

fbx_path = r"E:\Agent\TFTF-blender\3rd-party-models\transformers-galatic-trials-elita-one\source\Elita_One.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path)

print(f"\n=== Objects in Raw Sketchfab FBX ({len(bpy.data.objects)}) ===")
for obj in bpy.data.objects:
    print(f"[{obj.type:8s}] {obj.name}")
    if obj.type == 'MESH':
        print(f"   Vertices: {len(obj.data.vertices)}, Polygons: {len(obj.data.polygons)}")
        print(f"   Materials: {[m.name for m in obj.data.materials if m]}")
        print(f"   Vertex Groups: {len(obj.vertex_groups)}")
