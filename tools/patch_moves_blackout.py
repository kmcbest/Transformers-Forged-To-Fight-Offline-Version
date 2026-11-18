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
BLACKOUT_BULLET_FIRE_PID = -8888888888888888893
BLACKOUT_BULLET_EXPLODE_PID = -8888888888888888894

GALVATRON_S2_PID = -5777576223989766411
GALVATRON_FIRE_PID = -615518233694469998
GALVATRON_EXPLODE_PID = 1179416697310299179

RIGHT_PROP_PATH = (
    "character_model/Reference/Hips/Spine/Spine1/RightShoulder/"
    "RightArm/RightArmRoll/RightForeArm/RightForeArmRoll/RightHand/RightProp"
)

FX_RENAME_MAP = {
    "fx_p_galvatron_blast_streaks": "fx_p_blackout_blast_streaks",
    "fx_p_galvatron_charge_up": "fx_p_blackout_charge_up",
    "fx_p_galvatron_energy_ball": "fx_p_blackout_energy_ball",
    "fx_p_galvatron_blast_discharge": "fx_p_blackout_blast_discharge",
    "fx_p_galvatron_large_blast": "fx_p_blackout_large_blast",
    "fx_p_galvatron_large_projectile": "fx_p_blackout_large_projectile",
    "fx_p_galvatron_projectile_impact": "fx_p_blackout_projectile_impact",
    "projectile_galvatron_heavy_bullet": "projectile_blackout_energy_bullet",
}


def remap_event_fx(ev: dict, move_name: str) -> dict:
    ev["mn"] = move_name
    for key in ("pn", "dn"):
        val = ev.get(key)
        if isinstance(val, str) and val in FX_RENAME_MAP:
            ev[key] = FX_RENAME_MAP[val]
    # Remap Galvatron gun_barrel/FX attachment path to Blackout's RightHand/RightProp
    for rkey in ("ref", "atr"):
        ref_obj = ev.get(rkey)
        if isinstance(ref_obj, dict) and "gun_barrel" in str(ref_obj.get("r", "")):
            ev[rkey] = {"r": RIGHT_PROP_PATH, "t": 1}
            if ev.get("pn") == "fx_p_blackout_blast_streaks" and rkey == "atr":
                ev["po"] = {"o": {"x": 0.0, "y": 0.0, "z": 0.0}, "s": 1}
    return ev


def patch_moves_for_blackout():
    moves_path = Path("assets_redeco/moves.assetbundle")
    assert moves_path.exists(), f"Missing {moves_path}"
    env = UnityPy.load(str(moves_path))
    bf = list(env.files.values())[0]
    sf = list(env.assets)[0]

    # 1. Author move_blackout_special_01 from Galvatron S2 (move_galvatron_special_02)
    gal_s2_obj = sf.objects[GALVATRON_S2_PID]
    s1_tree = copy.deepcopy(gal_s2_obj.read_typetree())
    s1_tree["m_Name"] = "move_blackout_special_01"
    s1_data = json.loads(s1_tree["m_Script"])
    s1_data["moves"]["m_Name"] = "move_blackout_special_01"
    s1_events = []
    for ev in s1_data.get("moves", {}).get("events", []):
        ev = remap_event_fx(ev, "move_blackout_special_01")
        if "hd" in ev and isinstance(ev["hd"], dict):
            # 将源自惊破天 S2 的 attackLevel 从 32 (Special2) 修正为 16 (Special1)
            if ev["hd"].get("al") == 32:
                ev["hd"]["al"] = 16
            # 最后一击 (idx == 100) 设为不可防御 (Unblockable: 'u': True)
            if ev["hd"].get("idx") == 100:
                ev["hd"]["u"] = True
        s1_events.append(ev)
    s1_data["moves"]["events"] = s1_events
    s1_tree["m_Script"] = json.dumps(s1_data)

    new_s1 = copy.copy(gal_s2_obj)
    new_s1.path_id = BLACKOUT_S1_PID
    if hasattr(new_s1, "save_typetree"):
        new_s1.save_typetree(s1_tree)
    else:
        new_s1.write_typetree(s1_tree)
    sf.objects[BLACKOUT_S1_PID] = new_s1
    print(f"[+] Updated move_blackout_special_01 (PID {BLACKOUT_S1_PID}) <- Galvatron S2 (native purple FX)")

    # 2. Author move_blackout_heavy_bullet_fire
    gal_fire_obj = sf.objects[GALVATRON_FIRE_PID]
    fire_tree = copy.deepcopy(gal_fire_obj.read_typetree())
    fire_tree["m_Name"] = "move_blackout_heavy_bullet_fire"
    fire_data = json.loads(fire_tree["m_Script"])
    fire_data["moves"]["m_Name"] = "move_blackout_heavy_bullet_fire"
    fire_data["moves"]["events"] = [
        remap_event_fx(ev, "move_blackout_heavy_bullet_fire")
        for ev in fire_data.get("moves", {}).get("events", [])
    ]
    fire_tree["m_Script"] = json.dumps(fire_data)
    new_fire = copy.copy(gal_fire_obj)
    new_fire.path_id = BLACKOUT_BULLET_FIRE_PID
    if hasattr(new_fire, "save_typetree"):
        new_fire.save_typetree(fire_tree)
    else:
        new_fire.write_typetree(fire_tree)
    sf.objects[BLACKOUT_BULLET_FIRE_PID] = new_fire
    print(f"[+] Added move_blackout_heavy_bullet_fire (PID {BLACKOUT_BULLET_FIRE_PID})")

    # 3. Author move_blackout_heavy_bullet_explode
    gal_exp_obj = sf.objects[GALVATRON_EXPLODE_PID]
    exp_tree = copy.deepcopy(gal_exp_obj.read_typetree())
    exp_tree["m_Name"] = "move_blackout_heavy_bullet_explode"
    exp_data = json.loads(exp_tree["m_Script"])
    exp_data["moves"]["m_Name"] = "move_blackout_heavy_bullet_explode"
    exp_data["moves"]["events"] = [
        remap_event_fx(ev, "move_blackout_heavy_bullet_explode")
        for ev in exp_data.get("moves", {}).get("events", [])
    ]
    exp_tree["m_Script"] = json.dumps(exp_data)
    new_exp = copy.copy(gal_exp_obj)
    new_exp.path_id = BLACKOUT_BULLET_EXPLODE_PID
    if hasattr(new_exp, "save_typetree"):
        new_exp.save_typetree(exp_tree)
    else:
        new_exp.write_typetree(exp_tree)
    sf.objects[BLACKOUT_BULLET_EXPLODE_PID] = new_exp
    print(f"[+] Added move_blackout_heavy_bullet_explode (PID {BLACKOUT_BULLET_EXPLODE_PID})")

    # Remove unused move_blackout_special_02
    sf.objects.pop(BLACKOUT_S2_PID, None)

    # 4. Update AssetBundle container
    for obj in sf.objects.values():
        if obj.type.name == "AssetBundle":
            ab_tree = obj.read_typetree()
            container = ab_tree.get("m_Container", [])
            container = [c for c in container if "move_blackout_" not in c[0]]
            container.extend([
                [
                    "assets/bundles/movedata/move_blackout_special_01.txt",
                    {"preloadIndex": 0, "preloadSize": 0, "asset": {"m_FileID": 0, "m_PathID": BLACKOUT_S1_PID}},
                ],
                [
                    "assets/bundles/movedata/move_blackout_heavy_bullet_fire.txt",
                    {"preloadIndex": 0, "preloadSize": 0, "asset": {"m_FileID": 0, "m_PathID": BLACKOUT_BULLET_FIRE_PID}},
                ],
                [
                    "assets/bundles/movedata/move_blackout_heavy_bullet_explode.txt",
                    {"preloadIndex": 0, "preloadSize": 0, "asset": {"m_FileID": 0, "m_PathID": BLACKOUT_BULLET_EXPLODE_PID}},
                ],
            ])
            ab_tree["m_Container"] = container
            if hasattr(obj, "save_typetree"):
                obj.save_typetree(ab_tree)
            else:
                obj.write_typetree(ab_tree)
            print(f"[+] Updated AssetBundle container ({len(container)} total)")
            break

    # 5. Save moves.assetbundle with LZ4 compression
    moves_path.write_bytes(bf.save(packer="lz4"))
    print(f"[+] Re-saved {moves_path} cleanly!")


if __name__ == "__main__":
    patch_moves_for_blackout()
