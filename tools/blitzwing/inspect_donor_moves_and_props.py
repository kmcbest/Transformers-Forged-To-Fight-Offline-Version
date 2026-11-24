import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import json
from pathlib import Path
import UnityPy

MOVES_BUNDLE = Path(r"E:\Agent\TFTF-blender\assets_redeco\moves.assetbundle")
BLD_BUNDLE = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\bludgeon_gs_rd20_odr\bludgeon_gs_rd20.assetbundle")

env = UnityPy.load(str(MOVES_BUNDLE))
target_moves = {
    "move_attackRanged_handGun_left_XL_01",
    "move_attackRanged_handGun_left_XL_02",
    "move_attackRanged_handGun_left_XL_03B",
    "move_mixmaster_special_01",
    "move_bludgeon_special_02",
    "move_windblade_special_01",
    "move_sideswipe_special_02",
    "move_tactical_attack_light_01",
    "move_cheetor_attack_light_02",
    "move_military_attack_light_03",
    "move_military_attack_medium_02",
    "move_wheeljack_attack_medium_01",
    "move_kickback_attack_medium_02",
}

for o in env.objects:
    if o.type.name == "TextAsset":
        t = o.read()
        if t.m_Name in target_moves:
            raw = t.m_Script if isinstance(t.m_Script, str) else t.m_Script.decode("utf-8", errors="replace")
            data = json.loads(raw)
            print(f"\n=== {t.m_Name} (PID={o.path_id}) keys={list(data.keys())} ===")
            for k, v in data.items():
                if k in ("_evs", "evs", "_events"):
                    for e in v:
                        et = e.get("$type", "")
                        if any(x in et for x in ("Prop", "Particle", "Projectile", "Audio", "Sound")):
                            print(f"  [{et.split('.')[-1].split(',')[0]}] {e}")
                elif k != "hits":
                    print(f"  {k}={v}")

bld_env = UnityPy.load(str(BLD_BUNDLE))
bld_objs = {o.path_id: o for o in bld_env.objects}
print("\n=== BLUDGEON PropsController ===")
for o in bld_env.objects:
    if o.type.name == "MonoBehaviour":
        t = o.read_typetree()
        if "_props" in t:
            go = bld_objs[t["m_GameObject"]["m_PathID"]].read_typetree()
            print(f"  GO={go['m_Name']} PID={o.path_id}")
            for k, v in zip(t["_props"]["_serializedKeys"], t["_props"]["_serializedValues"]):
                print(f"    key={k} Name={v['Name']} InitFlags={v['InitFlags']} Root='{v['RootPath']}' Pos={v['PositionOffset']} Rot={v['RotationOffset']} inst={v['_instance']['m_PathID']} anim={v['_animator']['m_PathID']}")
