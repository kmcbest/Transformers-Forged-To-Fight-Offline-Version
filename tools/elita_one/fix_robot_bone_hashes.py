import sys
from pathlib import Path
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(r"E:\Agent\TFTF-blender")
elita_bundle_path = ROOT / "assets_redeco" / "elita_one_gs.assetbundle"
arcee_bundle_path = ROOT / "extracted_apk" / "assets" / "assetpack" / "arcee_gs_deluxe2014_odr" / "arcee_gs_deluxe2014.assetbundle"

print("[*] Loading Arcee base bundle...")
a_env = UnityPy.load(str(arcee_bundle_path))
arcee_hashes = []
for obj in a_env.objects:
    if obj.type.name == "Mesh" and obj.read_typetree().get("m_Name") == "cha_arcee_gs_deluxe2014_00":
        arcee_hashes = obj.read_typetree().get("m_BoneNameHashes", [])
        break

print(f"[+] Found {len(arcee_hashes)} ground-truth bone name hashes from Arcee.")

print("[*] Loading Elita One bundle...")
e_env = UnityPy.load(str(elita_bundle_path))

fixed = False
for obj in e_env.objects:
    if obj.type.name == "Mesh":
        tree = obj.read_typetree()
        if tree.get("m_Name") == "cha_arcee_gs_deluxe2014_00":
            old_hashes = tree.get("m_BoneNameHashes", [])
            print(f"[*] Robot Mesh old hashes: {len(old_hashes)} -> setting to {len(arcee_hashes)} Arcee hashes...")
            tree["m_BoneNameHashes"] = arcee_hashes
            obj.save_typetree(tree)
            fixed = True
            break

if not fixed:
    raise RuntimeError("Failed to find cha_arcee_gs_deluxe2014_00 in Elita bundle!")

print(f"[*] Saving updated bundle with packer='lz4'...")
bf = list(e_env.files.values())[0]
with open(elita_bundle_path, "wb") as f:
    f.write(bf.save(packer="lz4"))

size_mb = elita_bundle_path.stat().st_size / (1024 * 1024)
print(f"[✓] SUCCESS: Elita One bundle updated! Size: {size_mb:.2f} MB")
