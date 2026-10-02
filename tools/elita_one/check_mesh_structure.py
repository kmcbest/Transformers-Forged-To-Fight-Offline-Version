import bpy
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
FBX_PATH = ROOT / "3rd-party-models" / "transformers-galatic-trials-elita-one" / "source" / "Elita_One.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_PATH))

obj = bpy.data.objects.get("SK_CH_11.001")
print(f"SK_CH_11.001 verts: {len(obj.data.vertices)}, polys: {len(obj.data.polygons)}")

# Check duplicate vertices at same coordinates
coords = {}
for i, v in enumerate(obj.data.vertices):
    k = (round(v.co.x, 4), round(v.co.y, 4), round(v.co.z, 4))
    coords.setdefault(k, []).append(i)

dup_count = sum(1 for k, v in coords.items() if len(v) > 1)
print(f"Unique vertex positions: {len(coords)} out of {len(obj.data.vertices)} (duplicate position groups: {dup_count})")

# Look at material slots
for i, mat in enumerate(obj.data.materials):
    print(f"Material slot {i}: {mat.name if mat else 'None'}")
