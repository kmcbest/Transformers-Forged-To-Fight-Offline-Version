import json
import bpy
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
FBX_PATH = ROOT / "3rd-party-models" / "transformers-galatic-trials-elita-one" / "source" / "Elita_One.fbx"
MAPPING_FILE = ROOT / "tools" / "elita_one" / "elita_to_arcee_mapping.json"

with open(MAPPING_FILE, "r") as f:
    mapping = json.load(f)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_PATH))

obj = bpy.data.objects.get("SK_CH_11.001")
arm = bpy.data.objects.get("SK_CH_11")

print(f"Total vertex groups in mesh: {len(obj.vertex_groups)}")
print(f"Total bones in armature: {len(arm.data.bones)}")

unmapped_vgs = []
for vg in obj.vertex_groups:
    if vg.name not in mapping:
        vcount = sum(1 for v in obj.data.vertices if any(g.group == vg.index and g.weight > 0.001 for g in v.groups))
        unmapped_vgs.append((vg.name, vcount))

print(f"\nUnmapped Vertex Groups ({len(unmapped_vgs)}):")
for name, cnt in unmapped_vgs:
    print(f"  {name}: {cnt} verts")

unmapped_bones = []
for b in arm.data.bones:
    if b.name not in mapping:
        unmapped_bones.append(b.name)

print(f"\nUnmapped Armature Bones ({len(unmapped_bones)}):")
for name in unmapped_bones:
    print(f"  {name}")
