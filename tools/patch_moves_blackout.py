import copy
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

BLACKOUT_S1_PID = -8888888888888888891
BLACKOUT_S2_PID = -8888888888888888892

def patch_moves_for_blackout():
    moves_path = Path("assets_redeco/moves.assetbundle")
    assert moves_path.exists(), f"Missing {moves_path}"
    env = UnityPy.load(str(moves_path))
    bf = list(env.files.values())[0]
    sf = list(env.assets)[0]

    # Find Shockwave S1 & Ironhide S2
    sw_s1_obj = sf.objects[4201596759461759487]
    ih_s2_obj = sf.objects[2411174992823652744]

    # 1. Author move_blackout_special_01
    s1_tree = copy.deepcopy(sw_s1_obj.read_typetree())
    s1_tree["m_Name"] = "move_blackout_special_01"
    s1_data = json.loads(s1_tree["m_Script"])
    s1_data["moves"]["m_Name"] = "move_blackout_special_01"

    for ev in s1_data.get("moves", {}).get("events", []):
        ev_type = ev.get("type", "")
        pn = ev.get("pn", "")
        if ev_type == "ProjectileMoveEvent" and "laser" in pn:
            ev["pn"] = "projectile_grindor_missile"
            ev["dn"] = "projectile_grindor_missile"
            ev["oe"] = "explode_special"
            # Offset slightly to emerge from helicopter shoulder pod
            if "po" in ev and "o" in ev["po"]:
                ev["po"]["o"]["x"] = 0.0
                ev["po"]["o"]["y"] = 4.0
                ev["po"]["o"]["z"] = 5.0
        elif ev_type == "ParticleMoveEvent" and "muzzle_flash" in pn:
            ev["pn"] = "fx_p_heavy_projectile_ignition"
            ev["dn"] = "fx_p_heavy_projectile_ignition"

    s1_tree["m_Script"] = json.dumps(s1_data)
    new_s1 = copy.copy(sw_s1_obj)
    new_s1.path_id = BLACKOUT_S1_PID
    if hasattr(new_s1, "save_typetree"):
        new_s1.save_typetree(s1_tree)
    else:
        new_s1.write_typetree(s1_tree)
    sf.objects[BLACKOUT_S1_PID] = new_s1
    print(f"[+] Added move_blackout_special_01 (PID {BLACKOUT_S1_PID})")

    # 2. Author move_blackout_special_02
    s2_tree = copy.deepcopy(ih_s2_obj.read_typetree())
    s2_tree["m_Name"] = "move_blackout_special_02"
    s2_data = json.loads(s2_tree["m_Script"])
    s2_data["moves"]["m_Name"] = "move_blackout_special_02"

    for ev in s2_data.get("moves", {}).get("events", []):
        ev_type = ev.get("type", "")
        pn = ev.get("pn", "")
        if ev_type == "ProjectileMoveEvent":
            if "bullet" in pn:
                ev["pn"] = "projectile_grindor_bullet"
                ev["dn"] = "projectile_grindor_bullet"
                ev["oe"] = "explode_special"
            elif "grenade" in pn:
                ev["pn"] = "projectile_grindor_missile"
                ev["dn"] = "projectile_grindor_missile"
                ev["oe"] = "explode_special"
        elif ev_type == "ParticleMoveEvent":
            if "muzzle_flash" in pn:
                ev["pn"] = "fx_p_optimus_muzzle_flash"
                ev["dn"] = "fx_p_optimus_muzzle_flash"
            elif "charge" in pn:
                ev["pn"] = "fx_p_heavy_projectile_ignition"
                ev["dn"] = "fx_p_heavy_projectile_ignition"

    s2_tree["m_Script"] = json.dumps(s2_data)
    new_s2 = copy.copy(ih_s2_obj)
    new_s2.path_id = BLACKOUT_S2_PID
    if hasattr(new_s2, "save_typetree"):
        new_s2.save_typetree(s2_tree)
    else:
        new_s2.write_typetree(s2_tree)
    sf.objects[BLACKOUT_S2_PID] = new_s2
    print(f"[+] Added move_blackout_special_02 (PID {BLACKOUT_S2_PID})")

    # 3. Update AssetBundle container
    for obj in sf.objects.values():
        if obj.type.name == "AssetBundle":
            ab_tree = obj.read_typetree()
            container = ab_tree.get("m_Container", [])
            container = [c for c in container if "move_blackout_" not in c[0]]
            container.append([
                "assets/bundles/movedata/move_blackout_special_01.txt",
                {"preloadIndex": 0, "preloadSize": 0, "asset": {"m_FileID": 0, "m_PathID": BLACKOUT_S1_PID}}
            ])
            container.append([
                "assets/bundles/movedata/move_blackout_special_02.txt",
                {"preloadIndex": 0, "preloadSize": 0, "asset": {"m_FileID": 0, "m_PathID": BLACKOUT_S2_PID}}
            ])
            ab_tree["m_Container"] = container
            if hasattr(obj, "save_typetree"):
                obj.save_typetree(ab_tree)
            else:
                obj.write_typetree(ab_tree)
            print(f"[+] Updated AssetBundle container with Blackout moves ({len(container)} total)")
            break

    # 4. Save moves.assetbundle
    moves_path.write_bytes(bf.save(packer="lz4"))
    print(f"[+] Re-saved {moves_path} cleanly!")

if __name__ == "__main__":
    patch_moves_for_blackout()
