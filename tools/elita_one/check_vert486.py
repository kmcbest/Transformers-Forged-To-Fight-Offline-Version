import bpy
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
FBX_PATH = ROOT / "3rd-party-models" / "transformers-galatic-trials-elita-one" / "source" / "Elita_One.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_PATH))

obj = bpy.data.objects.get("SK_CH_11.001")
v = obj.data.vertices[486]
print(f"Vert 486 in FBX: co={v.co}, groups={[(obj.vertex_groups[g.group].name, g.weight) for g in v.groups]}")

# Also check other vertices in this part:
# Let's see all vertices with group names for 486..500
for vi in range(486, 495):
    v = obj.data.vertices[vi]
    print(f"Vert {vi}: co={v.co}, groups={[(obj.vertex_groups[g.group].name, g.weight) for g in v.groups]}")
