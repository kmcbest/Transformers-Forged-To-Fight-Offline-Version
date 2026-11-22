import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
import numpy as np

BUNDLE_PATH = r"assets_redeco/onslaught_gs.assetbundle"
env = UnityPy.load(BUNDLE_PATH)
obj_map = {obj.path_id: obj for obj in env.objects}

mesh = obj_map[243592621990493584].read_typetree()
submeshes = mesh.get("m_SubMeshes", [])
assert len(submeshes) == 2, f"Expected 2 submeshes, got {len(submeshes)}"
print(f"[PASS] Robot mesh has 2 submeshes: sm0={submeshes[0]['indexCount']}, sm1={submeshes[1]['indexCount']}")

for smr_pid in [3131805236270788271, 7476088394338840652]:
    smr = obj_map[smr_pid].read_typetree()
    mats = smr.get("m_Materials", [])
    assert len(mats) == 2, f"Expected 2 materials on SMR {smr_pid}, got {len(mats)}"
    assert mats[0]["m_PathID"] == 5474742503365929845
    assert mats[1]["m_PathID"] == -337851165086787921
    print(f"[PASS] SMR {smr_pid} correctly bound to [MAT_ROBOT, MAT_EYES]")

mat_rob = obj_map[5474742503365929845].read_typetree()
mat_rob_cols = dict(mat_rob["m_SavedProperties"]["m_Colors"])
print(f"[PASS] Robot mat emissive: {mat_rob_cols['_emissive_intensity_col']}")
assert mat_rob_cols['_emissive_intensity_col']['b'] == 1.0

mat_eyes = obj_map[-337851165086787921].read_typetree()
mat_eyes_cols = dict(mat_eyes["m_SavedProperties"]["m_Colors"])
print(f"[PASS] Eyes mat emissive: {mat_eyes_cols['_emissive_intensity_col']}")
assert mat_eyes_cols['_emissive_intensity_col']['r'] == 1.0
assert abs(mat_eyes_cols['_emissive_intensity_col']['b'] - 0.10) < 1e-3

mat_veh = obj_map[-304038823457699575].read_typetree()
mat_veh_cols = dict(mat_veh["m_SavedProperties"]["m_Colors"])
print(f"[PASS] Vehicle mat emissive: {mat_veh_cols['_emissive_intensity_col']}")
assert mat_veh_cols['_emissive_intensity_col']['b'] == 1.0

print("\n=== ALL ONSLAUGHT ASSERTIONS PASSED! ===")
