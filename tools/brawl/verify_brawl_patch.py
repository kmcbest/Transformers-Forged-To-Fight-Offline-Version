import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

BUNDLE_PATH = r"assets_redeco/brawl_gs.assetbundle"
env = UnityPy.load(BUNDLE_PATH)
obj_map = {obj.path_id: obj for obj in env.objects}

mesh = obj_map[8927022796776742380].read_typetree()
submeshes = mesh.get("m_SubMeshes", [])
assert len(submeshes) == 2, f"Expected 2 submeshes, got {len(submeshes)}"
print(f"[PASS] Robot mesh has 2 submeshes: sm0={submeshes[0]['indexCount']}, sm1={submeshes[1]['indexCount']}")

for smr_pid in [-1713043385139994820, 6657504797783083318]:
    smr = obj_map[smr_pid].read_typetree()
    mats = smr.get("m_Materials", [])
    assert len(mats) == 2, f"Expected 2 materials on SMR {smr_pid}, got {len(mats)}"
    assert mats[0]["m_PathID"] == 2758279787216392959
    assert mats[1]["m_PathID"] == -7854615674899395621
    print(f"[PASS] SMR {smr_pid} correctly bound to [MAT_ROBOT, MAT_EYES]")

mat_rob = obj_map[2758279787216392959].read_typetree()
mat_rob_cols = dict(mat_rob["m_SavedProperties"]["m_Colors"])
print(f"[PASS] Robot mat emissive: {mat_rob_cols['_emissive_intensity_col']}")
assert abs(mat_rob_cols['_emissive_intensity_col']['b'] - 1.0) < 1e-3

mat_eyes = obj_map[-7854615674899395621].read_typetree()
mat_eyes_cols = dict(mat_eyes["m_SavedProperties"]["m_Colors"])
print(f"[PASS] Eyes mat emissive: {mat_eyes_cols['_emissive_intensity_col']}")
assert abs(mat_eyes_cols['_emissive_intensity_col']['r'] - 1.0) < 1e-3
assert abs(mat_eyes_cols['_emissive_intensity_col']['b'] - 0.10) < 1e-3

mat_tank = obj_map[-8143696719442631496].read_typetree()
mat_tank_cols = dict(mat_tank["m_SavedProperties"]["m_Colors"])
print(f"[PASS] Tank mat emissive: {mat_tank_cols['_emissive_intensity_col']}")
assert abs(mat_tank_cols['_emissive_intensity_col']['b'] - 1.0) < 1e-3

print("\n=== ALL BRAWL ASSERTIONS PASSED! ===")
