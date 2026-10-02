import bpy
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
FBX_PATH = ROOT / "3rd-party-models" / "transformers-galatic-trials-elita-one" / "source" / "Elita_One.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_PATH))

arm = bpy.data.objects.get("SK_CH_11")
print(f"=== SK_CH_11 Bone Positions in FBX ===")
for b in arm.data.bones:
    head = b.head_local
    print(f"{b.name:32s} Head=({head.x:6.2f}, {head.y:6.2f}, {head.z:6.2f}) Parent={b.parent.name if b.parent else 'None'}")
