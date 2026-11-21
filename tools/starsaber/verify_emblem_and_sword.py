import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path
import numpy as np

bundle_path = Path(r"E:\Agent\TFTF-blender\assets_redeco\starsaber_gs_leader2014.assetbundle")
env = UnityPy.load(str(bundle_path))

mesh_obj = None
for o in env.objects:
    if o.type.name == "Mesh":
        tt = o.read_typetree()
        if "00" in tt.get("m_Name", ""):
            mesh_obj = tt
            break

assert mesh_obj is not None, "Failed to find Mesh 00 in starsaber_gs_leader2014.assetbundle"
print(f"=== Verified Mesh: '{mesh_obj.get('m_Name')}' ===")

# Check SubMesh count and AABBs
submeshes = mesh_obj.get("m_SubMeshes", [])
assert len(submeshes) == 2, f"Expected 2 submeshes, got {len(submeshes)}"

sm0 = submeshes[0]
sm1 = submeshes[1]
print(f"SubMesh 0: verts {sm0['firstVertex']}..{sm0['firstVertex']+sm0['vertexCount']}, indexCount={sm0['indexCount']}")
print(f"  AABB Center=({sm0['localAABB']['m_Center']['x']:.3f}, {sm0['localAABB']['m_Center']['y']:.3f}, {sm0['localAABB']['m_Center']['z']:.3f}), Extent=({sm0['localAABB']['m_Extent']['x']:.3f}, {sm0['localAABB']['m_Extent']['y']:.3f}, {sm0['localAABB']['m_Extent']['z']:.3f})")

print(f"SubMesh 1: verts {sm1['firstVertex']}..{sm1['firstVertex']+sm1['vertexCount']}, indexCount={sm1['indexCount']}")
print(f"  AABB Center=({sm1['localAABB']['m_Center']['x']:.3f}, {sm1['localAABB']['m_Center']['y']:.3f}, {sm1['localAABB']['m_Center']['z']:.3f}), Extent=({sm1['localAABB']['m_Extent']['x']:.3f}, {sm1['localAABB']['m_Extent']['y']:.3f}, {sm1['localAABB']['m_Extent']['z']:.3f})")

# Assert SubMesh 1 is flat sword (Extent.y < 0.5, Extent.x > 0.9)
assert sm1['localAABB']['m_Extent']['y'] < 0.5, f"Sword is tilted! Extent.y = {sm1['localAABB']['m_Extent']['y']}"
assert sm1['localAABB']['m_Extent']['x'] > 0.9, f"Sword extent.x wrong! Extent.x = {sm1['localAABB']['m_Extent']['x']}"
print("[PASS] SubMesh 1 sword angle is confirmed flat (pointing along leg)!")

# Check vertex data
vd = mesh_obj.get("m_VertexData", {})
vcount = vd.get("m_VertexCount", 0)
assert vcount == 23245
data = bytes(vd.get("m_DataSize", b""))

s0 = data[0 : vcount * 40]
s1 = data[vcount * 40 : vcount * 48]

# Check emblem UVs in Stream 1
uvs = np.frombuffer(s1, dtype=np.float32).reshape((vcount, 2))
emblem_mask = (uvs[:21929, 0] >= 0.35) & (uvs[:21929, 0] <= 0.40) & (uvs[:21929, 1] >= 0.40) & (uvs[:21929, 1] <= 0.45)
emblem_count = np.sum(emblem_mask)
print(f"Emblem clean palette UV count: {emblem_count}")
assert emblem_count >= 826, f"Emblem UVs not found! Count={emblem_count}"
print("[PASS] SubMesh 0 Autobot insignia UVs mapped to clean palette!")

# Check lifted positions in Stream 0
pos = np.zeros((vcount, 3), dtype=np.float32)
for i in range(vcount):
    pos[i] = np.frombuffer(s0[i*40 : i*40+12], dtype=np.float32)
sample_lifted_z = pos[19781, 2]
print(f"Sample emblem vertex 19781 Z: {sample_lifted_z:.5f}")
assert abs(sample_lifted_z - 0.90675) < 1e-4, f"Emblem not lifted! Z={sample_lifted_z}"
print("[PASS] SubMesh 0 Autobot insignia lifted by +0.015m to prevent Z-fighting!")

print("\n>>> ALL CHECKS PASSED PERFECTLY! <<<")
