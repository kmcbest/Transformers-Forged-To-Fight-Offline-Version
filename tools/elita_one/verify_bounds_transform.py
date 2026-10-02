import struct
from pathlib import Path
import UnityPy

ROOT = Path(r"E:\Agent\TFTF-blender")
elita_bundle = ROOT / "toolchain" / "unity_build_project" / "AssetBundles" / "elita_one_mesh.assetbundle"
arcee_bundle = ROOT / "extracted_apk" / "assets" / "assetpack" / "arcee_gs_deluxe2014_odr" / "arcee_gs_deluxe2014.assetbundle"

e_env = UnityPy.load(str(elita_bundle))
a_env = UnityPy.load(str(arcee_bundle))

for obj in a_env.objects:
    if obj.type.name == "Mesh" and obj.read_typetree().get("m_Name") == "cha_arcee_gs_deluxe2014_00":
        a_aabb = obj.read_typetree().get("m_LocalAABB")
        print("Arcee AABB Center:", a_aabb.get("m_Center"))
        print("Arcee AABB Extent:", a_aabb.get("m_Extent"))

for obj in e_env.objects:
    if obj.type.name == "Mesh" and obj.read_typetree().get("m_Name") == "cha_elita_one_gs_00":
        raw = obj.read_typetree().get("m_VertexData", {}).get("m_DataSize", b"")
        vc = obj.read_typetree().get("m_VertexData", {}).get("m_VertexCount", 0)
        stride = 40
        min_x, max_x = float('inf'), float('-inf')
        min_y, max_y = float('inf'), float('-inf')
        min_z, max_z = float('inf'), float('-inf')
        for i in range(vc):
            px, py, pz = struct.unpack_from("<3f", raw, i * stride)
            nx = px; ny = pz; nz = py
            min_x = min(min_x, nx); max_x = max(max_x, nx)
            min_y = min(min_y, ny); max_y = max(max_y, ny)
            min_z = min(min_z, nz); max_z = max(max_z, nz)
        print("\nTransformed Elita with (px, pz, py):")
        print(f"X: [{min_x:.3f}, {max_x:.3f}] Center: {(min_x+max_x)/2:.3f} Extent: {(max_x-min_x)/2:.3f}")
        print(f"Y: [{min_y:.3f}, {max_y:.3f}] Center: {(min_y+max_y)/2:.3f} Extent: {(max_y-min_y)/2:.3f}")
        print(f"Z: [{min_z:.3f}, {max_z:.3f}] Center: {(min_z+max_z)/2:.3f} Extent: {(max_z-min_z)/2:.3f}")
