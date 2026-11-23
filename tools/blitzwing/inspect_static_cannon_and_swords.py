import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import UnityPy
from pathlib import Path

ROOT_BL = Path(r"E:\Agent\TFTF-blender")
ROOT_GM = Path(r"E:\Agent\TFTF")

meg_env = UnityPy.load(str(ROOT_BL / "extracted_apk/assets/assetpack/megatron_gs_leader2015_odr/megatron_gs_leader2015.assetbundle"))
omap = {o.path_id: o for o in meg_env.objects}

def dump_go_tree(m, tr_pid, indent=0):
    tr = m[tr_pid].read_typetree()
    go_pid = tr["m_GameObject"]["m_PathID"]
    go = m[go_pid].read_typetree()
    comps = [f"{m[c['component']['m_PathID']].type.name}({c['component']['m_PathID']})" for c in go.get("m_Component", [])]
    print(f"{'  '*indent}- GO '{go['m_Name']}'({go_pid}) TR({tr_pid}) pos={tr['m_LocalPosition']} rot={tr['m_LocalRotation']} comps={comps}")
    for ch in tr.get("m_Children", []):
        dump_go_tree(m, ch["m_PathID"], indent+1)

print("=== Megatron staticCannon full trees ===")
for o in meg_env.objects:
    if o.type.name == "GameObject":
        go = o.read_typetree()
        if go["m_Name"] == "staticCannon":
            tr_pid = next(c["component"]["m_PathID"] for c in go["m_Component"] if omap[c["component"]["m_PathID"]].type.name == "Transform")
            dump_go_tree(omap, tr_pid)

print("\n=== Megatron Mace AOC & Animator ===")
for pid in (-5080088347447896440, 8370979346696130251, -1731553872345027617):
    if pid in omap:
        print(f"PID {pid} ({omap[pid].type.name}): {omap[pid].read_typetree()}")

print("\n=== Megatron All Weapon Materials ===")
for pid in (-9117353815363826346, 8075787426780741283, 1722215546450231611, 8175378592256487408):
    if pid in omap:
        mat = omap[pid].read_typetree()
        envs = {k: v["m_Texture"] for k, v in mat["m_SavedProperties"]["m_TexEnvs"]}
        print(f"  Mat {pid} '{mat['m_Name']}': tex={envs}")

print("\n=== Bludgeon Sword Props & Transform ===")
bld_env = UnityPy.load(str(ROOT_GM / "extracted_apk/assets/assetpack/bludgeon_gs_rd20_odr/bludgeon_gs_rd20.assetbundle"))
bld_map = {o.path_id: o for o in bld_env.objects}
for o in bld_env.objects:
    if o.type.name == "GameObject":
        go = o.read_typetree()
        if go["m_Name"] == "sword":
            tr_pid = next(c["component"]["m_PathID"] for c in go["m_Component"] if bld_map[c["component"]["m_PathID"]].type.name == "Transform")
            dump_go_tree(bld_map, tr_pid)
            break

print("\n=== Windblade Sword Props & Transform ===")
wb_env = UnityPy.load(str(ROOT_GM / "extracted_apk/assets/assetpack/windblade_gs_odr/windblade_gs.assetbundle"))
wb_map = {o.path_id: o for o in wb_env.objects}
for o in wb_env.objects:
    if o.type.name == "GameObject":
        go = o.read_typetree()
        if go["m_Name"] == "Sword":
            tr_pid = next(c["component"]["m_PathID"] for c in go["m_Component"] if wb_map[c["component"]["m_PathID"]].type.name == "Transform")
            dump_go_tree(wb_map, tr_pid)
            break

print("\n=== Check fx_p_red_projectile & fx_p_windblade & fx_p_mixmaster in bundles ===")
for label, path in [
    ("Megatron Externals", None),
    ("Mixmaster", ROOT_GM / "extracted_apk/assets/assetpack/mixmaster_cin_rotf_odr/mixmaster_cin_rotf.assetbundle"),
    ("Sideswipe", ROOT_BL / "extracted_apk/assets/assetpack/sideswipe_gs_odr/sideswipe_gs.assetbundle"),
]:
    if path is None: continue
    e = UnityPy.load(str(path))
    m = {o.path_id: o for o in e.objects}
    print(f"\n[{label}] PrefabList items:")
    for o in e.objects:
        if o.type.name == "GameObject":
            nm = o.read_typetree().get("m_Name", "")
            if any(x in nm.lower() for x in ("projectile", "fx_p_")):
                print(f"  GO {o.path_id}: {nm}")
