import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from pathlib import Path
import UnityPy

ROOT_GM = Path(r"E:\Agent\TFTF")
for name, rel in [
    ("MIXMASTER", "extracted_apk/assets/assetpack/mixmaster_cin_rotf_odr/mixmaster_cin_rotf.assetbundle"),
    ("SIDESWIPE", "extracted_apk/assets/assetpack/sideswipe_gs_deluxe2014_odr/sideswipe_gs_deluxe2014.assetbundle"),
]:
    p = ROOT_GM / rel
    if not p.exists():
        # try glob
        hits = list((ROOT_GM / "extracted_apk/assets/assetpack").glob(f"*{name.lower()}*/*.assetbundle"))
        p = hits[0] if hits else p
    print(f"\n=== {name}: {p.name} (exists={p.exists()}) ===")
    if not p.exists():
        continue
    env = UnityPy.load(str(p))
    objs = {o.path_id: o for o in env.objects}
    for o in env.objects:
        if o.type.name == "GameObject":
            go = o.read_typetree()
            if "projectile_" in go["m_Name"]:
                print(f"  Projectile GO '{go['m_Name']}' PID={o.path_id}")
                for c in go["m_Component"]:
                    cp = c["component"]["m_PathID"]
                    t = objs[cp].type.name
                    if t == "MonoBehaviour":
                        tt = objs[cp].read_typetree()
                        if "_moves" in tt:
                            mv_list = tt["_moves"]
                            if isinstance(mv_list, list):
                                print(f"    MoveSet list: {[(m.get('Name'), m.get('Move', m.get('MoveData', {}))) for m in mv_list]}")
                            else:
                                print(f"    MoveSet dict: {mv_list}")
                        elif "_prefabs" in tt:
                            print(f"    PrefabList: {[(e.get('Prefab', {}).get('m_FileID'), e.get('Prefab', {}).get('m_PathID'), e.get('Amount')) for e in tt['_prefabs']]}")
                        elif "CollisionPointOffset" in tt or "Speed" in tt:
                            print(f"    Projectile cfg: { {k:v for k,v in tt.items() if k in ('CollisionPointOffset','Radius','Speed','Gravity','MaxLifeTime')} }")
        elif o.type.name == "MonoBehaviour":
            tt = o.read_typetree()
            if "_prefabs" in tt:
                go = objs[tt["m_GameObject"]["m_PathID"]].read_typetree()
                if "projectile_" not in go["m_Name"]:
                    print(f"  Root PrefabList GO={go['m_Name']} count={len(tt['_prefabs'])} entries={[(e.get('Prefab',{}).get('m_FileID'), e.get('Prefab',{}).get('m_PathID')) for e in tt['_prefabs'][:12]]}")
