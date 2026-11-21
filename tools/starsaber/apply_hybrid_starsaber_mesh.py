import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import subprocess
import UnityPy
from pathlib import Path
import numpy as np

MESH_BUNDLE = Path(r"E:\Agent\TFTF-blender\3rd-party-models\StarSaber\04_unity_bundles\starsaber_mesh.assetbundle")

# 1. Load f3e2a9d (fixed emblem)
cmd_f3 = ["git", "-C", r"E:\Agent\TFTF-blender", "show", "f3e2a9d:3rd-party-models/StarSaber/04_unity_bundles/starsaber_mesh.assetbundle"]
res_f3 = subprocess.run(cmd_f3, stdout=subprocess.PIPE, check=True)
env_f3 = UnityPy.load(res_f3.stdout)
tt_f3 = [o.read_typetree() for o in env_f3.objects if o.type.name == "Mesh" and "00" in o.read_typetree().get("m_Name", "")][0]

# 2. Load 6f315e6 (flat sword)
cmd_6f = ["git", "-C", r"E:\Agent\TFTF-blender", "show", "6f315e6:3rd-party-models/StarSaber/04_unity_bundles/starsaber_mesh.assetbundle"]
res_6f = subprocess.run(cmd_6f, stdout=subprocess.PIPE, check=True)
env_6f = UnityPy.load(res_6f.stdout)
tt_6f = [o.read_typetree() for o in env_6f.objects if o.type.name == "Mesh" and "00" in o.read_typetree().get("m_Name", "")][0]

# Total vertices: 23245
# SubMesh 0: 0..21929 (count = 21929)
# SubMesh 1: 21929..23245 (count = 1316)
VCOUNT = 23245
SM0_VCOUNT = 21929
SM1_VCOUNT = 1316

S0_STRIDE = 40
S1_STRIDE = 8
S2_STRIDE = 32

data_f3 = bytes(tt_f3['m_VertexData']['m_DataSize'])
data_6f = bytes(tt_6f['m_VertexData']['m_DataSize'])

s0_f3 = data_f3[0 : VCOUNT * S0_STRIDE]
s1_f3 = data_f3[VCOUNT * S0_STRIDE : VCOUNT * (S0_STRIDE + S1_STRIDE)]
s2_f3 = data_f3[VCOUNT * (S0_STRIDE + S1_STRIDE) :]

s0_6f = data_6f[0 : VCOUNT * S0_STRIDE]
s1_6f = data_6f[VCOUNT * S0_STRIDE : VCOUNT * (S0_STRIDE + S1_STRIDE)]
s2_6f = data_6f[VCOUNT * (S0_STRIDE + S1_STRIDE) :]

# Splicing:
# Stream 0: SubMesh 0 from f3 (lifted emblem), SubMesh 1 from 6f (flat sword)
s0_hybrid = s0_f3[: SM0_VCOUNT * S0_STRIDE] + s0_6f[SM0_VCOUNT * S0_STRIDE :]

# Stream 1: SubMesh 0 from f3 (clean palette UVs), SubMesh 1 from 6f
s1_hybrid = s1_f3[: SM0_VCOUNT * S1_STRIDE] + s1_6f[SM0_VCOUNT * S1_STRIDE :]

# Stream 2: Same in both
s2_hybrid = s2_6f

data_hybrid = s0_hybrid + s1_hybrid + s2_hybrid
assert len(data_hybrid) == len(data_6f), f"Size mismatch: {len(data_hybrid)} vs {len(data_6f)}"

# Build hybrid typetree using 6f as base
tt_hybrid = dict(tt_6f)
tt_hybrid['m_VertexData']['m_DataSize'] = bytes(data_hybrid)

# Verify SubMesh 1 AABB is 6f's flat sword
sm1_aabb = tt_hybrid['m_SubMeshes'][1]['localAABB']
print(f"SubMesh 1 AABB: Center=({sm1_aabb['m_Center']['x']:.3f}, {sm1_aabb['m_Center']['y']:.3f}, {sm1_aabb['m_Center']['z']:.3f}), Extent=({sm1_aabb['m_Extent']['x']:.3f}, {sm1_aabb['m_Extent']['y']:.3f}, {sm1_aabb['m_Extent']['z']:.3f})")

# Verify emblem UVs in hybrid Stream 1
uvs_hybrid = np.frombuffer(s1_hybrid, dtype=np.float32).reshape((VCOUNT, 2))
emblem_mask = (uvs_hybrid[:SM0_VCOUNT, 0] >= 0.35) & (uvs_hybrid[:SM0_VCOUNT, 0] <= 0.40) & (uvs_hybrid[:SM0_VCOUNT, 1] >= 0.40) & (uvs_hybrid[:SM0_VCOUNT, 1] <= 0.45)
print(f"[✓] Emblem clean palette UV count in SubMesh 0: {np.sum(emblem_mask)}")
assert np.sum(emblem_mask) >= 826, f"Expected at least 826 emblem vertices, got {np.sum(emblem_mask)}"

# Verify lifted position in hybrid Stream 0
pos_hybrid = np.zeros((VCOUNT, 3), dtype=np.float32)
for i in range(VCOUNT):
    pos_hybrid[i] = np.frombuffer(s0_hybrid[i*40 : i*40+12], dtype=np.float32)
print(f"[✓] Sample lifted emblem vertex 19781 pos: {pos_hybrid[19781]} (Z=0.90675 vs unlifted 0.89175)")
assert abs(pos_hybrid[19781, 2] - 0.9067513) < 1e-4

# Load current starsaber_mesh.assetbundle and replace Mesh 00
env_cur = UnityPy.load(str(MESH_BUNDLE))
updated = False
for o in env_cur.objects:
    if o.type.name == "Mesh" and "00" in o.read_typetree().get("m_Name", ""):
        print("Injecting hybrid Mesh 00 into starsaber_mesh.assetbundle...")
        o.save_typetree(tt_hybrid)
        updated = True
        break
assert updated, "Failed to find Mesh 00 in starsaber_mesh.assetbundle!"

with open(MESH_BUNDLE, "wb") as f:
    f.write(env_cur.file.save(packer="lz4"))
print(f"[✓] Saved hybrid starsaber_mesh.assetbundle ({MESH_BUNDLE.stat().st_size} bytes, packer='lz4')")
