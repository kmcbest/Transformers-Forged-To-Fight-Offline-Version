import bpy
from pathlib import Path

bpy.ops.wm.read_factory_settings(use_empty=True)
fbx_path = Path("3rd-party-models/transformers-fall-of-cybertron-demolishor/source/transformers fall of cybertron Demolishor.fbx").resolve()
bpy.ops.import_scene.fbx(filepath=str(fbx_path))

print("=== All Objects in Original FBX ===")
for obj in bpy.data.objects:
    print(f"- {obj.name:40s} type={obj.type:10s} parent={obj.parent.name if obj.parent else 'None'}")
    if obj.type == 'MESH':
        print(f"    verts={len(obj.data.vertices)}, AABB Z=[{min(v.co.z for v in obj.data.vertices):.2f}, {max(v.co.z for v in obj.data.vertices):.2f}]")
