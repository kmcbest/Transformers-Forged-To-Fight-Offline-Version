import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
import numpy as np

BUNDLE_PATH = r"e:\Agent\TFTF-blender\assets_redeco\vortex_gs.assetbundle"
env = UnityPy.load(BUNDLE_PATH)
obj_map = {obj.path_id: obj for obj in env.objects}

def align16(n):
    return (n + 15) & ~15

# 1. Verify wpns_RAOE (3025951477767776163) is untouched (RAOE.B == 0 everywhere!)
wpns_raoe = np.array(obj_map[3025951477767776163].read().image.convert("RGB"))
assert wpns_raoe[:, :, 2].max() == 0, f"wpns_RAOE has unexpected emission max={wpns_raoe[:,:,2].max()}!"
print(f"[PASS] wpns_RAOE is 100% clean (RAOE.B max=0) — zero helicopter glow leakage!")

# 2. Verify Helicopter Mesh has 3 SubMeshes (5756 base, 4 emblem, 443 interior)
vh_m = obj_map[-2766188856892899435].read()
vh_tt = obj_map[-2766188856892899435].read_typetree()
sm = vh_tt["m_SubMeshes"]
assert len(sm) == 3, f"Expected 3 submeshes, got {len(sm)}"
assert sm[0]["indexCount"] == 5756 * 3
assert sm[1]["indexCount"] == 4 * 3
assert sm[2]["indexCount"] == 443 * 3
ib_vh = np.frombuffer(bytes(vh_m.m_IndexBuffer), dtype=np.uint16).reshape(-1, 3)
sm1_tris = ib_vh[5756 : 5756 + 4]
sm1_verts = set(sm1_tris.flatten().tolist())
assert sm1_verts == {171, 172, 173, 174, 175, 176, 177, 178}, f"Unexpected SubMesh 1 verts: {sm1_verts}!"
vc_vh = vh_m.m_VertexData.m_VertexCount
raw_vh = bytes(vh_m.m_VertexData.m_DataSize)
uv_vh = np.ndarray((vc_vh, 2), dtype=np.float32, buffer=raw_vh, strides=(8, 4), offset=align16(vc_vh*40))
for v in sorted(sm1_verts):
    u, vv = uv_vh[v]
    assert (abs(u - 0.002) < 1e-4 or abs(u - 0.498) < 1e-4 or abs(u - 0.502) < 1e-4 or abs(u - 0.998) < 1e-4), f"Bad UV on v{v}: {(u,vv)}"
print(f"[PASS] Helicopter Mesh has 3 clean SubMeshes (Base=5756, Emblem=4, Interior=443) & aligned s1_off UVs!")

# 3. Verify WrapU/WrapV & cleared m_StreamData on all replaced Texture2D slots
for pid, exp_wh, exp_wrap in [
    (6239694728433603131,  (1024, 512), 1), # emb_diff
    (-8672171104083879485, (1024, 512), 1), # emb_raoe
    (-8753204007397435811, (64, 64),    1), # emb_nm
    (5741437468734501436,  (512, 512),  0), # int_diff (vh_interior_mat)
    (-3179261496129805109, (512, 512),  0), # int_nm (vh_interior_n)
    (696671028566742258,   (256, 256),  0), # int_raoe
]:
    t = obj_map[pid].read()
    tt = obj_map[pid].read_typetree()
    assert tt["m_StreamData"]["size"] == 0, f"Tex {pid} still points to .resS: {tt['m_StreamData']}"
    assert (t.m_Width, t.m_Height) == exp_wh, f"Tex {pid} size {(t.m_Width, t.m_Height)} != {exp_wh}"
    ts = tt["m_TextureSettings"]
    assert ts["m_WrapU"] == exp_wrap and ts["m_WrapV"] == exp_wrap, f"Tex {pid} wrap={ts}"
print("[PASS] All 6 replaced Texture2Ds have m_StreamData cleared, exact sizes, and proper WrapModes!")

# 4. Verify Helicopter Materials & SMRs
mat_veh_tt = obj_map[-3423934603996225370].read_typetree()
mat_emb_tt = obj_map[-7619844944224089758].read_typetree()
mat_int_tt = obj_map[6154045054253613272].read_typetree()
assert mat_veh_tt["m_Shader"] == mat_emb_tt["m_Shader"] == mat_int_tt["m_Shader"]
for smr_pid in [-3058981427382277161, 6619623465709811202]:
    mats = [m["m_PathID"] for m in obj_map[smr_pid].read_typetree()["m_Materials"]]
    assert mats == [-3423934603996225370, -7619844944224089758, 6154045054253613272]
print("[PASS] Helicopter SMRs & 3 Materials share identical Vehicle PBR shader!")

# 5. Verify Robot Mesh SubMesh 1 & RAOE masks
rob_tt = obj_map[5703189533076905359].read_typetree()
rsm = rob_tt["m_SubMeshes"]
assert len(rsm) == 2 and rsm[0]["indexCount"] == 48804 and rsm[1]["indexCount"] == 30
rob_raoe = np.array(obj_map[-2574972184015167263].read().image.convert("RGB"))
assert rob_raoe[1840:1940, 1410:1470, 2].max() == 0
assert rob_raoe[1750:1796, 1080:1108, 2].max() == 0
assert rob_raoe[0:512, 1536:2048, 2].max() == 90
assert rob_raoe[1490:1700, 60:350, 2].max() > 120
print("[PASS] Robot Mesh & RAOE verified!")

print("\n=== ALL 3-SUBMESH VORTEX ASSERTIONS PASSED! ===")
