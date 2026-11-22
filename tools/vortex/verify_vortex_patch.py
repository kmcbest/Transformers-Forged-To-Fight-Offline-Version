import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
import numpy as np

BUNDLE_PATH = r"assets_redeco/vortex_gs.assetbundle"
env = UnityPy.load(BUNDLE_PATH)
obj_map = {obj.path_id: obj for obj in env.objects}

# 1. Verify Helicopter Mesh & SMRs
vh_mesh = obj_map[-2766188856892899435].read_typetree()
vh_submeshes = vh_mesh.get("m_SubMeshes", [])
assert len(vh_submeshes) == 2, f"Expected 2 submeshes on helicopter mesh, got {len(vh_submeshes)}"
print(f"[PASS] Helicopter mesh has 2 submeshes: sm0={vh_submeshes[0]['indexCount']}, sm1={vh_submeshes[1]['indexCount']}")

# Verify vertex offset and UVs of emblem vertices
vd = vh_mesh["m_VertexData"]
vc = vd["m_VertexCount"]
raw = bytes(vd["m_DataSize"])
pos = np.ndarray((vc, 3), dtype=np.float32, buffer=raw[:vc*40], strides=(40, 4), offset=0)
uv = np.ndarray((vc, 2), dtype=np.float32, buffer=raw[vc*40:vc*48], strides=(8, 4), offset=0)

# Check that emblem UVs are clean [0, 1]
for vi in [171, 172, 173, 174, 175, 176, 177, 178]:
    u, v = uv[vi]
    assert (u == 0.0 or u == 1.0) and (v == 0.0 or v == 1.0), f"Vertex {vi} UV={uv[vi]} not normalized!"
print("[PASS] Helicopter emblem vertices 171..178 have normalized clean [0, 1] UVs.")

for smr_pid in [-3058981427382277161, 6619623465709811202]:
    smr = obj_map[smr_pid].read_typetree()
    mats = smr.get("m_Materials", [])
    assert len(mats) == 2
    assert mats[0]["m_PathID"] == -3423934603996225370
    assert mats[1]["m_PathID"] == -7619844944224089758
    print(f"[PASS] Helicopter SMR {smr_pid} correctly bound to [MAT_VEHICLE, MAT_EMBLEM]")

# 2. Verify Robot Mesh & SMRs
rob_mesh = obj_map[5703189533076905359].read_typetree()
rob_submeshes = rob_mesh.get("m_SubMeshes", [])
assert len(rob_submeshes) == 2, f"Expected 2 submeshes on robot mesh, got {len(rob_submeshes)}"
print(f"[PASS] Robot mesh has 2 submeshes: sm0={rob_submeshes[0]['indexCount']}, sm1={rob_submeshes[1]['indexCount']}")

for smr_pid in [-3243551817942222242, -2776875793336503958]:
    smr = obj_map[smr_pid].read_typetree()
    mats = smr.get("m_Materials", [])
    assert len(mats) == 2
    assert mats[0]["m_PathID"] == 2433515842246304279
    assert mats[1]["m_PathID"] == -4921200029808501144
    print(f"[PASS] Robot SMR {smr_pid} correctly bound to [MAT_ROBOT, MAT_EYES]")

# 3. Verify Material Emissives
mat_rob = obj_map[2433515842246304279].read_typetree()
mat_rob_cols = dict(mat_rob["m_SavedProperties"]["m_Colors"])
print(f"[PASS] Robot mat emissive: {mat_rob_cols['_emissive_intensity_col']}")
assert abs(mat_rob_cols['_emissive_intensity_col']['b'] - 1.0) < 1e-3

mat_eyes = obj_map[-4921200029808501144].read_typetree()
mat_eyes_cols = dict(mat_eyes["m_SavedProperties"]["m_Colors"])
print(f"[PASS] Eyes mat emissive: {mat_eyes_cols['_emissive_intensity_col']}")
assert abs(mat_eyes_cols['_emissive_intensity_col']['r'] - 1.0) < 1e-3
assert abs(mat_eyes_cols['_emissive_intensity_col']['b'] - 0.10) < 1e-3

mat_veh = obj_map[-3423934603996225370].read_typetree()
mat_veh_cols = dict(mat_veh["m_SavedProperties"]["m_Colors"])
print(f"[PASS] Vehicle mat emissive: {mat_veh_cols['_emissive_intensity_col']}")
assert abs(mat_veh_cols['_emissive_intensity_col']['b'] - 1.0) < 1e-3

mat_emb = obj_map[-7619844944224089758].read_typetree()
mat_emb_cols = dict(mat_emb["m_SavedProperties"]["m_Colors"])
print(f"[PASS] Emblem mat emissive: {mat_emb_cols['_emissive_intensity_col']}")
assert abs(mat_emb_cols['_emissive_intensity_col']['b'] - 1.0) < 1e-3

print("\n=== ALL VORTEX ASSERTIONS PASSED! ===")
