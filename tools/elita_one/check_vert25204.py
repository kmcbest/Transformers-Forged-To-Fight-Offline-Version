import bpy
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
FBX_PATH = ROOT / "3rd-party-models" / "transformers-galatic-trials-elita-one" / "source" / "Elita_One.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_PATH))

obj = bpy.data.objects.get("SK_CH_11.001")
v = obj.data.vertices[25204]
print(f"Vert 25204 in FBX: co={v.co}, groups={[(obj.vertex_groups[g.group].name, g.weight) for g in v.groups]}")
