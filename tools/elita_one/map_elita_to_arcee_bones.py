import json
import bpy
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
FBX_PATH = ROOT / "3rd-party-models" / "transformers-galatic-trials-elita-one" / "source" / "Elita_One.fbx"
ARCEE_BONES_PATH = ROOT / "tools" / "elita_one" / "arcee_extracted" / "arcee_63_bones.json"

with open(ARCEE_BONES_PATH, "r") as f:
    arcee_bones = json.load(f)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_PATH))

arm_obj = bpy.data.objects.get("SK_CH_11")
elita_bones = [b.name for b in arm_obj.data.bones]

print(f"Elita One has {len(elita_bones)} bones.")
print(f"Arcee has {len(arcee_bones)} bones.")

# Print all Elita bones
for b in elita_bones:
    print(" ", b)
