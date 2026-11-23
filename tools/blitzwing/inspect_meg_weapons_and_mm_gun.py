import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import UnityPy
from pathlib import Path

ROOT_BL = Path(r"E:\Agent\TFTF-blender")
ROOT_GM = Path(r"E:\Agent\TFTF")

def dump_go_tree(omap, tr_pid, indent=0):
    tr = omap[tr_pid].read_typetree()
    go_pid = tr["m_GameObject"]["m_PathID"]
    go = omap[go_pid].read_typetree()
    comps = []
    for c in go.get("m_Component", []):
        cpid = c["component"]["m_PathID"]
        comps.append(f"{omap[cpid].type.name}({cpid})")
    print(f"{'  '*indent}- GO '{go['m_Name']}'({go_pid}) TR({tr_pid}) pos={tr['m_LocalPosition']} rot={tr['m_LocalRotation']} scale={tr['m_LocalScale']} comps={comps}")
    for ch in tr.get("m_Children", []):
        dump_go_tree(omap, ch["m_PathID"], indent+1)

# 1. Inspect Megatron staticCannon, mace, LeftHand, RightHand, CharAudio, Bullet, PrefabList
meg_env = UnityPy.load(str(ROOT_BL / "extracted_apk/assets/assetpack/megatron_gs_leader2015_odr/megatron_gs_leader2015.assetbundle"))
omap = {o.path_id: o for o in meg_env.objects}

print("=== Megatron LeftHand / RightHand / Weapon Trees ===")
for o in meg_env.objects:
    if o.type.name == "GameObject":
        go = o.read_typetree()
        if go["m_Name"] in ("LeftHand", "RightHand", "cha_megatron_gs_leader2015_wpns_cannon_right", "cha_megatron_gs_leader2015_wpns_mace_left"):
            tr_pid = next(c["component"]["m_PathID"] for c in go["m_Component"] if omap[c["component"]["m_PathID"]].type.name == "Transform")
            if go["m_Name"] in ("LeftHand", "RightHand"):
                print(f"\nHand {go['m_Name']} (GO={o.path_id}, TR={tr_pid}):")
                dump_go_tree(omap, tr_pid)
            else:
                tr = omap[tr_pid].read_typetree()
                fpid = tr["m_Father"]["m_PathID"]
                fname = omap[omap[fpid].read_typetree()["m_GameObject"]["m_PathID"]].read_typetree()["m_Name"]
                print(f"\nWeapon '{go['m_Name']}' father='{fname}'({fpid}) TR={tr_pid}")
                dump_go_tree(omap, tr_pid)

print("\n=== Megatron CharacterAudio ===")
for o in meg_env.objects:
    if o.type.name == "MonoBehaviour":
        tt = o.read_typetree()
        if "_genEvent" in str(tt) or "_categories" in tt:
            print(f"CharacterAudio PID={o.path_id}: categories={tt.get('_categories')}")
            for ev in tt.get("_events", []):
                if ev.get("_override") or "projectile" in ev.get("_genEvent", ""):
                    print(f"  {ev}")

print("\n=== Megatron AudioClips (projectile/special) ===")
for o in meg_env.objects:
    if o.type.name == "AudioClip":
        tt = o.read_typetree()
        nm = tt.get("m_Name", "")
        if "projectile" in nm.lower() or "special" in nm.lower():
            print(f"  AudioClip {o.path_id}: '{nm}' len={tt.get('m_Length'):.3f} res={tt.get('m_Resource')}")

print("\n=== Megatron Root PrefabList ===")
for o in meg_env.objects:
    if o.type.name == "MonoBehaviour":
        tt = o.read_typetree()
        if "PrefabList" in tt:
            print(f"PrefabList PID={o.path_id} (len={len(tt['PrefabList'])}):")
            for it in tt["PrefabList"]:
                p = it["Prefab"]
                fid, pid = p["m_FileID"], p["m_PathID"]
                nm = omap[pid].read_typetree().get("m_Name", "") if (fid == 0 and pid in omap) else ""
                print(f"  ({fid}, {pid}) '{nm}' amt={it['Amount']}")

print("\n=== Megatron Projectile_megatron_gs_bullet ===")
for pid in (9003878510878022874, 4196009027374098921):
    go = omap[pid].read_typetree()
    print(f"GO '{go['m_Name']}' ({pid}):")
    for c in go["m_Component"]:
        cpid = c["component"]["m_PathID"]
        co = omap[cpid]
        print(f"  comp {co.type.name}({cpid}): { {k:v for k,v in co.read_typetree().items() if k != 'm_GameObject'} }")

# 2. Check Motormaster Gun Prop exact structure
print("\n=== Motormaster Gun Prop ===")
mm_env = UnityPy.load(str(ROOT_GM / "extracted_apk/assets/assetpack/motormaster_gs_voyager2015_odr/motormaster_gs_voyager2015.assetbundle"))
mm_map = {o.path_id: o for o in mm_env.objects}
for o in mm_env.objects:
    if o.type.name == "MonoBehaviour":
        tt = o.read_typetree()
        if "_props" in tt:
            for k, v in zip(tt["_props"]["_serializedKeys"], tt["_props"]["_serializedValues"]):
                if "gun" in k.lower() or "blaster" in k.lower():
                    print(f"  MM PropsCtrl({o.path_id}) '{k}': InitFlags={v.get('InitFlags')} RootPath='{v.get('RootPath')}' Pos={v.get('PositionOffset')} Rot={v.get('RotationOffset')} AOC={v.get('OverrideController')} Renderers={v.get('_renderers')}")
    elif o.type.name == "GameObject":
        go = o.read_typetree()
        if go["m_Name"].lower() == "gun":
            tr_pid = next(c["component"]["m_PathID"] for c in go["m_Component"] if mm_map[c["component"]["m_PathID"]].type.name == "Transform")
            dump_go_tree(mm_map, tr_pid)
            break
