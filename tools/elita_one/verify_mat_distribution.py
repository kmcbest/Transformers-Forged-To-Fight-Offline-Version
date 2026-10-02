import bpy
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
FBX_PATH = ROOT / "3rd-party-models" / "transformers-galatic-trials-elita-one" / "source" / "Elita_One.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_PATH))

mesh = bpy.data.objects.get("SK_CH_11.001")

# Check materials
print("Raw FBX materials:", [m.name for m in mesh.data.materials])
# Check polygon material indices distribution
counts = {}
for p in mesh.data.polygons:
    counts[p.material_index] = counts.get(p.material_index, 0) + 1
print("Polygon counts per slot:", counts)
