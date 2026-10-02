import bpy
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
FBX_PATH = ROOT / "3rd-party-models" / "transformers-galatic-trials-elita-one" / "source" / "Elita_One.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_PATH))

mesh = bpy.data.objects.get("SK_CH_11.001")
print(f"Materials on raw FBX mesh: {[m.name for m in mesh.data.materials]}")
counts = {}
for p in mesh.data.polygons:
    counts[p.material_index] = counts.get(p.material_index, 0) + 1
print(f"Polygon counts per slot on raw FBX: {counts}")
