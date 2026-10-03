import sys
from pathlib import Path
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(r"E:\Agent\TFTF-blender")
elita_bundle = ROOT / "assets_redeco" / "elita_one_gs.assetbundle"
arcee_bundle = ROOT / "extracted_apk" / "assets" / "assetpack" / "arcee_gs_deluxe2014_odr" / "arcee_gs_deluxe2014.assetbundle"

e_env = UnityPy.load(str(elita_bundle))
a_env = UnityPy.load(str(arcee_bundle))

for obj in a_env.objects:
    if obj.type.name == "Mesh" and obj.read_typetree().get("m_Name") == "cha_arcee_gs_deluxe2014_00":
        a_tree = obj.read_typetree()
        a_hashes = a_tree.get("m_BoneNameHashes", [])

for obj in e_env.objects:
    if obj.type.name == "Mesh" and obj.read_typetree().get("m_Name") == "cha_arcee_gs_deluxe2014_00":
        e_tree = obj.read_typetree()
        e_hashes = e_tree.get("m_BoneNameHashes", [])

print(f"Arcee hashes count: {len(a_hashes)}")
print(f"Elita hashes count: {len(e_hashes)}")
print("Hashes diff:")
for i in range(max(len(a_hashes), len(e_hashes))):
    ah = a_hashes[i] if i < len(a_hashes) else None
    eh = e_hashes[i] if i < len(e_hashes) else None
    if ah != eh:
        print(f"Index {i:2d}: Arcee={ah} != Elita={eh}")
