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
        aabb = t.get("m_LocalAABB", {})
        mesh_results[name] = {
            "vc": vc,
            "bps": len(bps),
            "hashes": len(hashes),
            "hashes_list": hashes,
            "center": aabb.get("m_Center", {}),
            "extent": aabb.get("m_Extent", {})
        }

print("\n1. Mesh Verification:")
r_mesh = mesh_results.get("cha_arcee_gs_deluxe2014_00")
print(f"  Robot Mesh (cha_arcee_gs_deluxe2014_00):")
print(f"    Vertex count: {r_mesh['vc']} (expected 52432)")
print(f"    BindPoses: {r_mesh['bps']} (expected 63)")
print(f"    BoneHashes: {r_mesh['hashes']} (expected 63)")
r_matched = sum(1 for h in r_mesh['hashes_list'] if h in r_avatar_tos)
print(f"    TOS match: {r_matched} / {r_mesh['hashes']}")
c_y = r_mesh['center'].get('y', 0.0)
c_z = r_mesh['center'].get('z', 0.0)
print(f"    Center bounds: Y={c_y:.3f} (Upright ~4.42m), Z={c_z:.3f}")
assert r_mesh['vc'] == 52432
assert r_mesh['bps'] == 63
assert r_mesh['hashes'] == 63
assert r_matched == 63
assert c_y > 3.0, f"FATAL: Robot Mesh is lying down! Center Y={c_y}"
assert abs(c_z) < 1.0, f"FATAL: Robot Mesh has swapped Z/Y axes! Center Z={c_z}"

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
            c_y = t.get("m_AABB", {}).get("m_Center", {}).get("y", 0.0)
            assert c_y > 3.0, f"FATAL: SMR {obj.path_id} is lying down! Center Y={c_y}"
            print(f"  SMR {obj.path_id} ({label}): bones={len(bones)}, mats={mats}, Center Y={c_y:.3f}")
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
