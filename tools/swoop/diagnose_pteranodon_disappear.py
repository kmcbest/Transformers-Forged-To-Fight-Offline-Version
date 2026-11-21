import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import UnityPy
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
SWOOP = ROOT / "assets_redeco/swoop_gs_deluxe2008.assetbundle"
e = UnityPy.load(str(SWOOP))
omap = {o.path_id: o for o in e.objects}

print("=== 1. Inspect BOTH transformed subtrees in generated swoop_gs_deluxe2008.assetbundle ===")
def dump_tree(go_pid, depth=0):
    gtt = omap[go_pid].read_typetree()
    gname = gtt["m_Name"]
    comps = []
    tr_tt = None
    for c in gtt["m_Component"]:
        co = omap.get(c["component"]["m_PathID"])
        if not co:
            continue
        if co.type.name == "Transform":
            tr_tt = co.read_typetree()
        elif co.type.name == "SkinnedMeshRenderer":
            st = co.read_typetree()
            comps.append(f"SMR(PID={co.path_id}, en={st['m_Enabled']}, mesh={st['m_Mesh']['m_PathID']}, mats={[m['m_PathID'] for m in st['m_Materials']]}, rootBone={st['m_RootBone']['m_PathID']}, bones={len(st['m_Bones'])})")
        elif co.type.name == "Animator":
            at = co.read_typetree()
            comps.append(f"Animator(PID={co.path_id}, en={at['m_Enabled']}, ctrl={at['m_Controller']}, av={at['m_Avatar']})")
    pos = tr_tt["m_LocalPosition"]
    sca = tr_tt["m_LocalScale"]
    print("  " * depth + f"GO '{gname}' (PID={go_pid}, active={gtt['m_IsActive']}, pos=({pos['x']:.2f},{pos['y']:.2f},{pos['z']:.2f}), sca=({sca['x']:.2f},{sca['y']:.2f},{sca['z']:.2f})) {comps}")
    for ch in tr_tt["m_Children"]:
        ch_tr = omap.get(ch["m_PathID"])
        if ch_tr:
            dump_tree(ch_tr.read_typetree()["m_GameObject"]["m_PathID"], depth + 1)

for root_pid in (1529847556182042256, -4280993829309278178):
    print(f"\n--- Prefab {root_pid} ---")
    # find transformed
    stack = [root_pid]
    while stack:
        gp = stack.pop()
        gt = omap[gp].read_typetree()
        if gt["m_Name"] == "transformed":
            dump_tree(gp, 0)
            continue
        for c in gt["m_Component"]:
            co = omap.get(c["component"]["m_PathID"])
            if co and co.type.name == "Transform":
                for ch in co.read_typetree()["m_Children"]:
                    stack.append(omap[ch["m_PathID"]].read_typetree()["m_GameObject"]["m_PathID"])

print("\n=== 2. Check Vehicle SMR (_01) Parent GO, Bones & Material ===")
for spid in (-1331665652208216405, 4450385079657545705):
    st = omap[spid].read_typetree()
    b0_pid = st["m_Bones"][0]["m_PathID"]
    b0_tr = omap[b0_pid].read_typetree()
    b0_go = omap[b0_tr["m_GameObject"]["m_PathID"]].read_typetree()
    mat_pid = st["m_Materials"][0]["m_PathID"]
    mtt = omap[mat_pid].read_typetree()
    print(f"SMR {spid}: bone[0]='{b0_go['m_Name']}' (pos={b0_tr['m_LocalPosition']}, sca={b0_tr['m_LocalScale']}), m_Enabled={st['m_Enabled']}, AABB={st['m_AABB']}, updateOffscreen={st['m_UpdateWhenOffscreen']}")
    print(f"  Mat {mat_pid} floats={[(k,v) for k,v in mtt['m_SavedProperties']['m_Floats'] if 'mode' in k.lower() or 'zwrite' in k.lower() or 'emissive' in k.lower()]}")

print("\n=== 3. Check Swoop_Vehicle_WingFlap_transformed clip curves / m_LocalScale ===")
clip = omap[7111222233334444555].read_typetree()
print("Clip name:", clip["m_Name"], "stopTime:", clip["m_MuscleClip"]["m_StopTime"], "useHighQuality:", clip["m_UseHighQualityCurve"])
gen = clip["m_ClipBindingConstant"]["genericBindings"]
print("Bindings:", [(b["path"], b["attribute"], b["typeID"]) for b in gen])
