import bpy
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
FBX = ROOT / "toolchain" / "unity_build_project" / "Assets" / "ElitaOne" / "elita_one_prepared.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX))

print(f"=== Objects in {FBX.name} ===")
for obj in bpy.data.objects:
    print(f"  [{obj.type:10s}] {obj.name:30s}")
    if obj.type == "ARMATURE":
        print(f"    Bones: {len(obj.data.bones)}")
        print(f"    Sample bones: {[b.name for b in obj.data.bones[:10]]}")
    elif obj.type == "MESH":
        print(f"    Vertices: {len(obj.data.vertices)}, VGs: {len(obj.vertex_groups)}")
