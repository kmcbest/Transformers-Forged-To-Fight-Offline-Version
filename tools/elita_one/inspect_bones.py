import bpy
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
FBX_PATH = ROOT / "3rd-party-models" / "transformers-galatic-trials-elita-one" / "source" / "Elita_One.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_PATH))

arm = bpy.data.objects.get("SK_CH_11")
print(f"=== Bones in SK_CH_11 ({len(arm.data.bones)}) ===")
for b in arm.data.bones:
    p = b.parent.name if b.parent else "None"
    print(f"Bone: {b.name}, Parent: {p}")
