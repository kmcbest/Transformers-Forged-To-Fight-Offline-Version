import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import copy
import json
from pathlib import Path
import UnityPy

MOVES_BUNDLE = Path(r"E:\Agent\TFTF-blender\assets_redeco\moves.assetbundle")
SWOOP_HEAVY_PID = -7777777777777777701


def patch_swoop_heavy():
    print(f"Loading {MOVES_BUNDLE}...")
    env = UnityPy.load(str(MOVES_BUNDLE))
    moves_file = list(env.assets)[0]

    # 1. Check total moves count >= 945
    text_assets = [o for o in moves_file.objects.values() if o.type.name == "TextAsset"]
    initial_count = len(text_assets)
    print(f"Initial TextAssets count: {initial_count}")
    assert initial_count >= 945, f"CRITICAL: moves count {initial_count} < 945!"

    # 2. Find move_heavy_starscream_shoot as Seeker airborne flight template
    star_obj = None
    for o in text_assets:
        try:
            d = o.read_typetree()
            if d.get("m_Name") == "move_heavy_starscream_shoot":
                star_obj = o
                break
        except Exception:
            pass
    assert star_obj is not None, "Could not find move_heavy_starscream_shoot in moves.assetbundle!"

    star_tt = star_obj.read_typetree()
    star_script = json.loads(star_tt["m_Script"])

    # 3. Create move_heavy_swoop based on Starscream's mid-air Heavy hover + Grimlock's Fireball
    swoop_tt = copy.deepcopy(star_tt)
    swoop_tt["m_Name"] = "move_heavy_swoop"

    swoop_script = copy.deepcopy(star_script)
    swoop_moves = swoop_script.get("moves", {})
    swoop_moves["id"] = "move_heavy_swoop"

    new_events = []
    for ev in swoop_moves.get("events", []):
        # Drop Starscream's Rotor PropMoveEvent (not present on Ramjet/Swoop skeleton)
        if ev.get("type") == "PropMoveEvent" and ev.get("p") == "Rotor":
            continue
        ev["mn"] = "move_heavy_swoop"
        if ev.get("type") == "ParticleMoveEvent" and ev.get("pn") == "fx_p_heavy_projectile_ignition":
            print("Updating fx_p_heavy_projectile_ignition to 1.53x Swoop airborne beak mouth pos (0.0, 11.6, 2.3)...")
            ev["ref"] = {"r": "", "t": 2}
            ev["atr"] = {"r": "", "t": 2}
            ev["po"] = {"o": {"x": 0.0, "y": 11.6, "z": 2.3}, "s": 1}
        elif ev.get("type") == "ProjectileMoveEvent":
            print("Updating ProjectileMoveEvent to Grimlock fireball from 1.53x Swoop airborne beak mouth pos (0.0, 11.4, 2.8)...")
            ev["ref"] = {"r": "", "t": 2}
            ev["atr"] = {"r": "Hips", "t": 0}
            ev["po"] = {"o": {"x": 0.0, "y": 11.4, "z": 2.8}, "s": 1}
            ev["pn"] = "projectile_grimlock_fireball"
            ev["dn"] = "projectile_grimlock_fireball"
        new_events.append(ev)

    swoop_moves["events"] = new_events
    swoop_script["moves"] = swoop_moves
    swoop_tt["m_Script"] = json.dumps(swoop_script, indent=2)

    # 4. Insert or update in moves_file
    swoop_reader = copy.copy(star_obj)
    swoop_reader.path_id = SWOOP_HEAVY_PID
    moves_file.objects[SWOOP_HEAVY_PID] = swoop_reader
    swoop_reader.save_typetree(swoop_tt)

    # 5. Update AssetBundle container
    ab_obj = next((o for o in moves_file.objects.values() if o.type.name == "AssetBundle"), None)
    if ab_obj:
        ab_tree = ab_obj.read_typetree()
        container = ab_tree.get("m_Container", [])
        container = [c for c in container if "move_heavy_swoop" not in c[0]]
        container.append([
            "assets/bundles/movedata/move_heavy_swoop.txt",
            {"preloadIndex": 0, "preloadSize": 0, "asset": {"m_FileID": 0, "m_PathID": SWOOP_HEAVY_PID}}
        ])
        ab_tree["m_Container"] = container
        ab_obj.save_typetree(ab_tree)

    # 6. Save bundle with packer="lz4"
    print("Saving patched moves.assetbundle with packer='lz4'...")
    with open(MOVES_BUNDLE, "wb") as f:
        f.write(env.file.save(packer="lz4"))

    # 7. Reload and verify
    env_verify = UnityPy.load(str(MOVES_BUNDLE))
    v_file = list(env_verify.assets)[0]
    v_assets = [o for o in v_file.objects.values() if o.type.name == "TextAsset"]
    final_count = len(v_assets)
    print(f"Final TextAssets count: {final_count}")
    assert final_count >= 945, f"CRITICAL: final moves count {final_count} < 945!"

    found_swoop = False
    for o in v_assets:
        if o.path_id == SWOOP_HEAVY_PID:
            tt = o.read_typetree()
            assert tt.get("m_Name") == "move_heavy_swoop"
            scr = json.loads(tt["m_Script"])
            projs = [e for e in scr["moves"]["events"] if e.get("type") == "ProjectileMoveEvent"]
            assert len(projs) == 1
            assert projs[0]["pn"] == "projectile_grimlock_fireball"
            assert projs[0]["po"]["o"] == {"x": 0.0, "y": 11.4, "z": 2.8}
            found_swoop = True
            break
    assert found_swoop, "move_heavy_swoop not found after reload verification!"
    print("✅ [PASS] move_heavy_swoop (Starscream mid-air height + Grimlock fireball) verified in moves.assetbundle!")


if __name__ == "__main__":
    patch_swoop_heavy()
