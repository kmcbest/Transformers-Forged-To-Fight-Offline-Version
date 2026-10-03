import sys
from pathlib import Path
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(r"E:\Agent\TFTF-blender")
elita_bundle_path = ROOT / "assets_redeco" / "elita_one_gs.assetbundle"
arcee_bundle_path = ROOT / "extracted_apk" / "assets" / "assetpack" / "arcee_gs_deluxe2014_odr" / "arcee_gs_deluxe2014.assetbundle"

print("[*] Loading Arcee bundle...")
a_env = UnityPy.load(str(arcee_bundle_path))
a_smr_aabbs = {}
for obj in a_env.objects:
    if obj.type.name == "SkinnedMeshRenderer":
        t = obj.read_typetree()
        a_smr_aabbs[obj.path_id] = t.get("m_AABB")

print("[*] Loading Elita One bundle...")
e_env = UnityPy.load(str(elita_bundle_path))

updated = 0
for obj in e_env.objects:
    if obj.type.name == "SkinnedMeshRenderer" and obj.path_id in a_smr_aabbs:
        t = obj.read_typetree()
        old_aabb = t.get("m_AABB")
        new_aabb = a_smr_aabbs[obj.path_id]
        if old_aabb != new_aabb:
            print(f"[*] Calibrating SMR {obj.path_id} AABB:")
            print(f"    Old Center: {old_aabb.get('m_Center')}")
            print(f"    New Center: {new_aabb.get('m_Center')}")
            t["m_AABB"] = new_aabb
            obj.save_typetree(t)
            updated += 1

if updated > 0:
    print(f"[*] Saving {updated} updated SMRs with packer='lz4'...")
    bf = list(e_env.files.values())[0]
    with open(elita_bundle_path, "wb") as f:
        f.write(bf.save(packer="lz4"))
    print(f"[✓] Successfully calibrated SMR AABBs in {elita_bundle_path.name}!")
else:
    print("[*] No SMR AABBs needed calibration.")
