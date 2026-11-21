import sys
import zlib
import UnityPy

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

env = UnityPy.load(r"E:\Agent\TFTF-blender\assets_redeco\swoop_gs_deluxe2008.assetbundle")
objs = {o.path_id: o for o in env.objects}

# 1. Verify ALL 29 vehicle bone hashes & bindposes vs donor Ramjet
renv = UnityPy.load(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\ramjet_gs_deluxe2008_odr\ramjet_gs_deluxe2008.assetbundle")
robjs = {o.path_id: o for o in renv.objects}
r_mesh = robjs[733405694182770835].read_typetree()
s_mesh = objs[733405694182770835].read_typetree()
s_smr = objs[4450385079657545705].read()

print("=== Vehicle 29-bone check ===")
print(f"Donor m_BoneNameHashes == Swoop m_BoneNameHashes: {r_mesh['m_BoneNameHashes'] == s_mesh['m_BoneNameHashes']}")
print(f"Donor len(m_BindPose)={len(r_mesh['m_BindPose'])}, Swoop len(m_BindPose)={len(s_mesh['m_BindPose'])}")
# Check if bindPoses are reasonable (diagonal scale ~0.945 and no NaNs/zeros)
for i in range(len(s_mesh["m_BindPose"])):
    bp = s_mesh["m_BindPose"][i]
    rbp = r_mesh["m_BindPose"][i]
    tr = objs[s_smr.m_Bones[i].m_PathID].read()
    go = objs[tr.m_GameObject.m_PathID].read()
    if i < 5 or abs(bp["e00"]) < 1e-4 and abs(bp["e01"]) < 1e-4 and abs(bp["e02"]) < 1e-4:
        print(f"  [{i:2d}] {go.m_Name:28s} swoop_bp_diag=({bp['e00']:.3f},{bp['e11']:.3f},{bp['e22']:.3f}) t=({bp['e03']:.2f},{bp['e13']:.2f},{bp['e23']:.2f}) | ramjet_t=({rbp['e03']:.2f},{rbp['e13']:.2f},{rbp['e23']:.2f})")

# 2. Check Vehicle SMR RenderSettings, Layer, Renderer m_IsActive of transformed & children
def check_hierarchy(go_pid, depth=0):
    go = objs[go_pid].read_typetree()
    comps = []
    tr_tt = None
    for c in go["m_Component"]:
        co = objs[c["component"]["m_PathID"]]
        comps.append(f"{co.type.name}({co.path_id})")
        if co.type.name == "Transform":
            tr_tt = co.read_typetree()
    print(f"{'  '*depth}{go['m_Name']} (active={go['m_IsActive']}, layer={go['m_Layer']}) comps={comps}")
    if tr_tt and depth < 3:
        for ch in tr_tt["m_Children"]:
            c_tr = objs[ch["m_PathID"]].read_typetree()
            check_hierarchy(c_tr["m_GameObject"]["m_PathID"], depth + 1)

print("\n=== transformed GameObject hierarchy ===")
check_hierarchy(7693429312995989932)

# 3. Check Jet AOC & Fight AOC base controllers
jet_aoc = objs[-6340484879223379266].read_typetree()
fight_aoc = objs[6432204470035570307].read_typetree()
print("\nJet AOC base m_Controller:", jet_aoc["m_Controller"])
print("Fight AOC base m_Controller:", fight_aoc["m_Controller"])

# 4. Compare Swoop_Vehicle_WingFlap_transformed vs Ramjet_Normal_attackHeavy_transformed genericBindings
aenv = UnityPy.load(r"E:\Agent\TFTF-blender\assets_netflix\character_anim_procedural.assetbundle")
aobjs = {o.path_id: o for o in aenv.objects}

# Check all CRC hashes of vehicle hierarchy paths in swoop
path_by_crc = {}
def collect_paths(go_pid, prefix=""):
    go = objs[go_pid].read_typetree()
    for c in go["m_Component"]:
        co = objs[c["component"]["m_PathID"]]
        if co.type.name == "Transform":
            tr = co.read_typetree()
            for ch in tr["m_Children"]:
                ctr = objs[ch["m_PathID"]].read_typetree()
                cgo = objs[ctr["m_GameObject"]["m_PathID"]].read_typetree()
                p = f"{prefix}/{cgo['m_Name']}" if prefix else cgo["m_Name"]
                crc = zlib.crc32(p.encode("utf-8")) & 0xffffffff
                path_by_crc[crc] = p
                collect_paths(ctr["m_GameObject"]["m_PathID"], p)

collect_paths(7693429312995989932)
swoop_clip = objs[7111222233334444555].read_typetree()
print(f"\n=== Swoop_Vehicle_WingFlap_transformed bindings ({len(swoop_clip['m_ClipBindingConstant']['genericBindings'])}) ===")
for b in swoop_clip["m_ClipBindingConstant"]["genericBindings"]:
    p = path_by_crc.get(b["path"], f"UNKNOWN({b['path']})")
    print(f"  attr={b['attribute']} type={b['typeID']} path={p}")

ramjet_heavy_t = aobjs[2235498278053343569].read_typetree()
print(f"\n=== Ramjet_Normal_attackHeavy_transformed bindings ({len(ramjet_heavy_t['m_ClipBindingConstant']['genericBindings'])}) ===")
for b in ramjet_heavy_t["m_ClipBindingConstant"]["genericBindings"][:20]:
    p = path_by_crc.get(b["path"], f"UNKNOWN({b['path']})")
    print(f"  attr={b['attribute']} type={b['typeID']} path={p}")
