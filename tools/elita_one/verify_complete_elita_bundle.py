import sys
from pathlib import Path
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(r"E:\Agent\TFTF-blender")
elita_bundle = ROOT / "assets_redeco" / "elita_one_gs.assetbundle"
arcee_bundle = ROOT / "extracted_apk" / "assets" / "assetpack" / "arcee_gs_deluxe2014_odr" / "arcee_gs_deluxe2014.assetbundle"

print("==================== VERIFYING ELITA ONE BUNDLE ====================")
env = UnityPy.load(str(elita_bundle))
a_env = UnityPy.load(str(arcee_bundle))

# Get Arcee Avatar TOS tables
r_avatar_tos = {}
v_avatar_tos = {}
for obj in a_env.objects:
    if obj.type.name == "Avatar":
        t = obj.read_typetree()
        if t.get("m_Name") == "cha_arcee_gs_deluxe2014_00Avatar":
            r_avatar_tos = dict(t.get("m_TOS", []))
        elif t.get("m_Name") == "cha_arcee_gs_deluxe2014_01Avatar":
            v_avatar_tos = dict(t.get("m_TOS", []))

# 1. Check Meshes
mesh_results = {}
for obj in env.objects:
    if obj.type.name == "Mesh":
        t = obj.read_typetree()
        name = t.get("m_Name")
        vc = t.get("m_VertexData", {}).get("m_VertexCount", 0)
        bps = t.get("m_BindPose", [])
        hashes = t.get("m_BoneNameHashes", [])
        mesh_results[name] = {
            "vc": vc,
            "bps": len(bps),
            "hashes": len(hashes),
            "hashes_list": hashes
        }

print("\n1. Mesh Verification:")
r_mesh = mesh_results.get("cha_arcee_gs_deluxe2014_00")
print(f"  Robot Mesh (cha_arcee_gs_deluxe2014_00):")
print(f"    Vertex count: {r_mesh['vc']} (expected 52432)")
print(f"    BindPoses: {r_mesh['bps']} (expected 63)")
print(f"    BoneHashes: {r_mesh['hashes']} (expected 63)")
r_matched = sum(1 for h in r_mesh['hashes_list'] if h in r_avatar_tos)
print(f"    TOS match: {r_matched} / {r_mesh['hashes']}")
assert r_mesh['vc'] == 52432
assert r_mesh['bps'] == 63
assert r_mesh['hashes'] == 63
assert r_matched == 63

v_mesh = mesh_results.get("cha_arcee_gs_deluxe2014_01")
print(f"\n  Vehicle Mesh (cha_arcee_gs_deluxe2014_01):")
print(f"    Vertex count: {v_mesh['vc']} (expected 17886)")
print(f"    BindPoses: {v_mesh['bps']} (expected 25)")
print(f"    BoneHashes: {v_mesh['hashes']} (expected 25)")
v_matched = sum(1 for h in v_mesh['hashes_list'] if h in v_avatar_tos)
print(f"    TOS match: {v_matched} / {v_mesh['hashes']}")
assert v_mesh['vc'] == 17886
assert v_mesh['bps'] == 25
assert v_mesh['hashes'] == 25
assert v_matched == 25

# 2. Check SMRs
print("\n2. SMR Verification:")
for obj in env.objects:
    if obj.type.name == "SkinnedMeshRenderer":
        t = obj.read_typetree()
        bones = t.get("m_Bones", [])
        mats = [m.get("m_PathID") for m in t.get("m_Materials", [])]
        if len(bones) == 63:
            label = "P1 Robot" if obj.path_id == 8283545308434878436 else "P2 Robot"
            print(f"  SMR {obj.path_id} ({label}): bones={len(bones)}, mats={mats}")
        elif len(bones) == 25:
            label = "P1 Vehicle" if obj.path_id == -4178002549372221558 else "P2 Vehicle"
            print(f"  SMR {obj.path_id} ({label}): bones={len(bones)}, mats={mats}")

# 3. Check Textures
print("\n3. Texture Verification:")
for obj in env.objects:
    if obj.type.name == "Texture2D":
        t = obj.read_typetree()
        name = t.get("m_Name")
        if name in ["tform_misc_A", "tform_misc_NM", "wpns_RAOE", "cha_arcee_gs_deluxe2014_main_a", "main_NM", "main_tform_misc_RAOE"]:
            w = t.get("m_Width")
            h = t.get("m_Height")
            fmt = t.get("m_TextureFormat")
            print(f"  Texture {name:32s}: {w}x{h} (format {fmt})")

print(f"\nBundle size: {elita_bundle.stat().st_size / (1024*1024):.2f} MB")
print("\n[✓] ALL CHECKS PASSED PERFECTLY!")
