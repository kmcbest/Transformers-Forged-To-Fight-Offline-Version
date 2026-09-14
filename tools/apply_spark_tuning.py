#!/usr/bin/env python3
"""
apply_spark_tuning.py

Applies the fine-tuned physical hit spark parameters to character_fx.assetbundle and moves.assetbundle.
Parameters can be tuned visually in tools/spark_tuner.html and injected here.
"""

import sys
import zipfile
import json
import copy
import argparse
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    import UnityPy
except ImportError:
    print("UnityPy is required: pip install UnityPy lz4")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
APK_PATH = ROOT / "com.kabam.bigrobot_9.2.0-123129100_minAPI23(arm64-v8a,armeabi-v7a)(nodpi)_apkmirror.com.apk"
REDECO_DIR = ROOT / "assets_redeco"
REDECO_DIR.mkdir(exist_ok=True)

TARGET_FX_BUNDLE = REDECO_DIR / "character_fx.assetbundle"
TARGET_PROCEDURAL_BUNDLE = REDECO_DIR / "character_fx_procedural.assetbundle"
TARGET_MOVES_BUNDLE = REDECO_DIR / "moves.assetbundle"


def patch_character_fx_procedural(col_r: float, col_g: float, col_b: float):
    print(f"\n>>> Patching character_fx_procedural.assetbundle materials with deep forge color:")
    print(f"    Target Emissive Color=({col_r:.3f}, {col_g:.3f}, {col_b:.3f})")

    with zipfile.ZipFile(APK_PATH, "r") as zf:
        raw_data = zf.read("assets/assetpack/characters_fx_procedural_odr/character_fx_procedural.assetbundle")

    env = UnityPy.load(raw_data)
    patched_mats = 0

    target_mat_names = (
        "flat_sparks", "hit_sparks", "cyclonus_flat", "grimlock_flat_sparks"
    )

    for obj in env.objects:
        if obj.type.name == "Material":
            raw = obj.read_typetree()
            mname = raw.get("m_Name", "")
            if any(k in mname for k in target_mat_names):
                col_props = raw.get("m_SavedProperties", {}).get("m_Colors", [])
                modified = False
                for cp in col_props:
                    prop_name = cp[0] if isinstance(cp, (list, tuple)) else cp.get("first")
                    if prop_name in ["_emissive_intensity_col", "_TintColor"]:
                        target_dict = cp[1] if isinstance(cp, (list, tuple)) else cp.get("second")
                        target_dict["r"] = float(col_r)
                        target_dict["g"] = float(col_g)
                        target_dict["b"] = float(col_b)
                        target_dict["a"] = 1.0
                        modified = True
                if modified:
                    obj.save_typetree(raw)
                    patched_mats += 1
                    print(f"    - Patched material: {mname}")

    print(f"  [+] Patched {patched_mats} materials in character_fx_procedural")
    saved_bytes = env.file.save(packer="lz4")
    TARGET_PROCEDURAL_BUNDLE.write_bytes(saved_bytes)
    print(f"  [+] Saved {TARGET_PROCEDURAL_BUNDLE} ({len(saved_bytes) / 1024 / 1024:.2f} MB, LZ4 compressed)")


def patch_character_fx(speed: float, gravity: float, length_scale: float, burst: int,
                       col_r: float, col_g: float, col_b: float, shape_mode: str):
    print(f"\n>>> Patching character_fx.assetbundle with physics:")
    print(f"    Speed={speed}, Gravity={gravity}, LengthScale={length_scale}, Burst={burst}")
    print(f"    Color=({col_r:.3f}, {col_g:.3f}, {col_b:.3f}), Shape={shape_mode}")

    # Always extract cleanly from base APK to ensure pristine base
    with zipfile.ZipFile(APK_PATH, "r") as zf:
        raw_data = zf.read("assets/assetpack/characters/character_fx.assetbundle")

    env = UnityPy.load(raw_data)

    go_map = {}
    for obj in env.objects:
        if obj.type.name == "GameObject":
            go_map[obj.path_id] = obj.read_typetree().get("m_Name", "")

    target_gos = (
        "fx_p_spark_particles_wide", "centre_sparks", "sparks_shower",
        "sparks_shower_rear", "forward_sparks", "fx_p_hit_small", "fx_p_hit_sparks_small"
    )

    patched_ps = 0
    patched_psr = 0
    patched_mats = 0

    # 1. Update ParticleSystems
    for obj in env.objects:
        tname = obj.type.name
        if tname == "ParticleSystem":
            raw = obj.read_typetree()
            g_pid = raw.get("m_GameObject", {}).get("m_PathID")
            gname = go_map.get(g_pid, "")

            if gname in target_gos or "spark" in gname.lower():
                raw["playOnAwake"] = True
                raw["looping"] = False

                init = raw.get("InitialModule", {})
                init["maxNumParticles"] = max(init.get("maxNumParticles", 40), 600)

                # Set StartSpeed (physics ejection - compact explosion)
                spd = init.get("startSpeed", {})
                if isinstance(spd, dict):
                    spd["scalar"] = float(speed)
                    if "minScalar" in spd:
                        spd["minScalar"] = float(speed * 0.30)

                # Set Lifetime (crisp bursts)
                life = init.get("startLifetime", {})
                if isinstance(life, dict):
                    life["scalar"] = 0.65
                    if "minScalar" in life:
                        life["minScalar"] = 0.30

                # Set GravityModifier (strong downward forge curve)
                grav = init.get("gravityModifier", {})
                if isinstance(grav, dict):
                    grav["scalar"] = float(gravity)
                    if "minScalar" in grav:
                        grav["minScalar"] = float(gravity)

                # Inject particle vertex startColor (deep red-orange forge glow)
                sc = init.get("startColor", {})
                if isinstance(sc, dict):
                    col_dict = {"r": float(col_r), "g": float(col_g), "b": float(col_b), "a": 1.0}
                    sc["minColor"] = col_dict
                    sc["maxColor"] = col_dict
                    if "maxGradient" in sc and isinstance(sc["maxGradient"], dict):
                        sc["maxGradient"]["key0"] = col_dict
                        sc["maxGradient"]["key1"] = col_dict
                    if "minGradient" in sc and isinstance(sc["minGradient"], dict):
                        sc["minGradient"]["key0"] = col_dict
                        sc["minGradient"]["key1"] = col_dict

                # Set Emitter Shape
                shape = raw.get("ShapeModule", {})
                if shape and isinstance(shape, dict):
                    if shape_mode == "sphere":
                        shape["type"] = 4  # Sphere
                    elif shape_mode == "wide_cone":
                        shape["type"] = 0  # Cone
                        shape["angle"] = 85.0
                    else:  # cone
                        shape["type"] = 0  # Cone
                        shape["angle"] = 65.0

                # Set Bursts
                em = raw.get("EmissionModule", {})
                bursts = em.get("m_Bursts", [])
                if bursts:
                    for b in bursts:
                        cc = b.get("countCurve", {})
                        if "scalar" in cc:
                            cc["scalar"] = float(burst)
                        if "minScalar" in cc:
                            cc["minScalar"] = float(burst * 0.7)

                obj.save_typetree(raw)
                patched_ps += 1

        elif tname == "ParticleSystemRenderer":
            raw = obj.read_typetree()
            g_pid = raw.get("m_GameObject", {}).get("m_PathID")
            gname = go_map.get(g_pid, "")

            if gname in target_gos or "spark" in gname.lower():
                mats = raw.get("m_Materials", [])
                clean_mats = [m for m in mats if m.get("m_PathID") != 0]
                if clean_mats:
                    raw["m_Materials"] = clean_mats

                raw["m_RenderMode"] = 1  # Stretched Billboard
                raw["m_LengthScale"] = float(length_scale)
                raw["m_VelocityScale"] = -0.02

                obj.save_typetree(raw)
                patched_psr += 1

        elif tname == "Material":
            raw = obj.read_typetree()
            mname = raw.get("m_Name", "")
            if any(k in mname for k in ["flat_sparks", "hit_sparks", "cyclonus_flat"]):
                col_props = raw.get("m_SavedProperties", {}).get("m_Colors", [])
                for cp in col_props:
                    prop_name = cp[0] if isinstance(cp, (list, tuple)) else cp.get("first")
                    if prop_name in ["_emissive_intensity_col", "_TintColor", "_Color"]:
                        target_dict = cp[1] if isinstance(cp, (list, tuple)) else cp.get("second")
                        if prop_name == "_emissive_intensity_col":
                            target_dict["r"] = float(col_r)
                            target_dict["g"] = float(col_g)
                            target_dict["b"] = float(col_b)
                            target_dict["a"] = 1.0
                obj.save_typetree(raw)
                patched_mats += 1

    print(f"  [+] Patched {patched_ps} ParticleSystems, {patched_psr} Renderers, {patched_mats} Materials")
    saved_bytes = env.file.save(packer="lz4")
    TARGET_FX_BUNDLE.write_bytes(saved_bytes)
    print(f"  [+] Saved {TARGET_FX_BUNDLE} ({len(saved_bytes) / 1024 / 1024:.2f} MB, LZ4 compressed)")


LIFELINE_S1_PID = -8888888888888888881
LIFELINE_S2_PID = -8888888888888888882


def inject_lifeline_moves(env):
    for obj in env.objects:
        if obj.type.name == "TextAsset":
            d = obj.read()
            if getattr(d, "m_Name", "") == "move_lifeline_special_01":
                return  # Already present

    moves_file = list(env.file.files.values())[0]

    ab_obj = None
    for obj in env.objects:
        if obj.type.name == "AssetBundle":
            ab_obj = obj
            break

    kb_reader = None
    rt_reader = None
    for obj in env.objects:
        if obj.type.name == "TextAsset":
            mname = obj.read().m_Name
            if mname == "move_kickback_special_01":
                kb_reader = obj
            elif mname == "move_ratchet_special_02":
                rt_reader = obj

    if not kb_reader or not rt_reader:
        print("  [-] Warning: Could not find template moves for Lifeline")
        return

    # Clone Lifeline S1 (based on Kickback S1)
    s1_move = copy.deepcopy(kb_reader.read_typetree())
    s1_move["m_Name"] = "move_lifeline_special_01"
    s1_data = json.loads(s1_move["m_Script"])
    s1_data["moves"]["m_Name"] = "move_lifeline_special_01"

    s1_events = []
    for ev in s1_data.get("moves", {}).get("events", []):
        if ev.get("type") in ["PropMoveEvent", "PlayPropAnimatorStateMoveEvent"]:
            continue
        pn = ev.get("pn", "")
        if "laser_beam" in pn:
            ev["pn"] = "fx_p_laser_beam"
            ev["dn"] = "fx_p_laser_beam"
            ev["d"] = 15
            if "po" in ev and "o" in ev["po"]:
                ev["po"]["o"]["x"] = -0.8
                ev["po"]["o"]["y"] = 0.0
                ev["po"]["o"]["z"] = 0.25
            if "ro" in ev and "o" in ev["ro"]:
                is_mirrored = any(
                    sc.get("type") == "MoveEventCondition_IsMirrored" and sc.get("inv") is False
                    for sc in ev.get("sc", [])
                )
                ev["ro"]["o"]["x"] = 0.0
                ev["ro"]["o"]["z"] = 0.0
                ev["ro"]["o"]["y"] = 290.0 if is_mirrored else 110.0
        elif "dash" in pn:
            ev["pn"] = "fx_r_dash_trail"
        s1_events.append(ev)

    s1_data["moves"]["events"] = s1_events
    s1_move["m_Script"] = json.dumps(s1_data)
    s1_reader = copy.copy(kb_reader)
    s1_reader.path_id = LIFELINE_S1_PID
    moves_file.objects[LIFELINE_S1_PID] = s1_reader
    s1_reader.save_typetree(s1_move)

    # Clone Lifeline S2 (based on Ratchet S2)
    s2_move = copy.deepcopy(rt_reader.read_typetree())
    s2_move["m_Name"] = "move_lifeline_special_02"
    s2_data = json.loads(s2_move["m_Script"])
    s2_data["moves"]["m_Name"] = "move_lifeline_special_02"

    s2_events = []
    for ev in s2_data.get("moves", {}).get("events", []):
        if ev.get("type") in ["PropMoveEvent", "PlayPropAnimatorStateMoveEvent"]:
            continue

        pn = ev.get("pn", "")
        if "powerup_ring" in pn:
            ev["pn"] = "fx_p_laser_beam_particulates_circle"
            ev["dn"] = "fx_p_laser_beam_particulates_circle"
            ev["d"] = 45
            if "po" in ev and "o" in ev["po"]:
                ev["po"]["o"]["x"] = 0.0
                ev["po"]["o"]["y"] = 1.2
                ev["po"]["o"]["z"] = 0.0
        elif "powerup" in pn:
            ev["pn"] = "fx_p_shockwave_powerup"
            ev["dn"] = "fx_p_shockwave_powerup"
            ev["d"] = 30
            if "po" in ev and "o" in ev["po"]:
                ev["po"]["o"]["x"] = 0.0
                ev["po"]["o"]["y"] = 1.2
                ev["po"]["o"]["z"] = 0.0
        elif "body_charge" in pn:
            ev["pn"] = "fx_p_shockwave_body_charge"
        elif "chest_charge" in pn:
            ev["pn"] = "fx_p_blast_charge"
        elif "wrench_blur" in pn:
            ev["pn"] = "fx_r_arcee_trail"

        s_ev = json.dumps(ev)
        if "leftGun" in s_ev or "wrench" in s_ev:
            s_ev = s_ev.replace("leftGun/Reference/COG/FX", "swordLeft")
            s_ev = s_ev.replace("wrench/cha_ratchet_gs_kabam_wpns_wrench", "swordRight")
            ev = json.loads(s_ev)

        s2_events.append(ev)

    s2_data["moves"]["events"] = s2_events
    s2_move["m_Script"] = json.dumps(s2_data)
    s2_reader = copy.copy(rt_reader)
    s2_reader.path_id = LIFELINE_S2_PID
    moves_file.objects[LIFELINE_S2_PID] = s2_reader
    s2_reader.save_typetree(s2_move)

    if ab_obj:
        ab_tree = ab_obj.read_typetree()
        container = ab_tree.get("m_Container", [])
        container = [c for c in container if "move_lifeline_special" not in c[0]]
        container.append([
            "assets/bundles/movedata/move_lifeline_special_01.txt",
            {"preloadIndex": 0, "preloadSize": 0, "asset": {"m_FileID": 0, "m_PathID": LIFELINE_S1_PID}}
        ])
        container.append([
            "assets/bundles/movedata/move_lifeline_special_02.txt",
            {"preloadIndex": 0, "preloadSize": 0, "asset": {"m_FileID": 0, "m_PathID": LIFELINE_S2_PID}}
        ])
        ab_tree["m_Container"] = container
        ab_obj.save_typetree(ab_tree)

    print("  [+] Injected Lifeline dedicated moves (move_lifeline_special_01 & 02)")


def patch_chromia_hit_events(env):
    target_moves = [
        "move_heavy_arcee_donut",
        "move_agile_attack_light_01",
        "move_agile_attack_light_02",
        "move_agile_attack_light_03",
        "move_agile_attack_light_04",
        "move_agile_attack_medium_01",
        "move_agile_attack_medium_02"
    ]
    patched = 0
    for obj in env.objects:
        if obj.type.name == "TextAsset":
            d = obj.read()
            mname = getattr(d, "m_Name", "")
            if mname in target_moves:
                text = getattr(d, "m_Script", "")
                try:
                    js = json.loads(text)
                    events = js.get("moves", {}).get("events", [])
                    has_hit_vfx = False
                    for ev in events:
                        if ev.get("pn") == "fx_p_hit_large_no_local":
                            ev["d"] = 15
                            ev["inf"] = False
                            has_hit_vfx = True
                        elif ev.get("pn") in ("fx_p_hit_small", "fx_p_hit_medium"):
                            ev["pn"] = "fx_p_hit_large_no_local"
                            ev["d"] = 12
                            ev["inf"] = False
                            has_hit_vfx = True
                    if not has_hit_vfx:
                        for ev in events:
                            if ev.get("type") == "HitMoveEvent":
                                hit_frame = ev.get("f", 4)
                                events.append({
                                    "type": "ParticleMoveEvent",
                                    "pn": "fx_p_hit_large_no_local",
                                    "f": hit_frame,
                                    "d": 12,
                                    "inf": False,
                                    "tar": 0,
                                    "po": {"x": 0, "y": 4.5, "z": 4.0},
                                    "ro": {"x": 0, "y": 0, "z": 0},
                                    "cos": False,
                                    "mn": mname,
                                    "dn": f"ParticleMoveEvent_Sparks_{hit_frame}",
                                    "id": -999000 - hit_frame
                                })
                                break
                    d.m_Script = json.dumps(js)
                    d.save()
                    patched += 1
                except Exception:
                    pass
    print(f"  [+] Patched Chromia attack hit spark events in {patched} moves")


def patch_moves():
    print(f"\n>>> Assembling and patching moves.assetbundle (Netflix complete edition base)...")
    netflix_bundle = ROOT / "assets_netflix" / "moves.assetbundle"
    if netflix_bundle.exists():
        print(f"  [*] Loading base moves from {netflix_bundle}")
        raw_data = netflix_bundle.read_bytes()
    elif TARGET_MOVES_BUNDLE.exists():
        print(f"  [*] Loading base moves from {TARGET_MOVES_BUNDLE}")
        raw_data = TARGET_MOVES_BUNDLE.read_bytes()
    else:
        print("  [-] Error: assets_netflix/moves.assetbundle not found!")
        sys.exit(1)

    env = UnityPy.load(raw_data)

    # 1. Inject Lifeline moves if not present
    inject_lifeline_moves(env)

    # 2. Patch Chromia hit spark events
    patch_chromia_hit_events(env)

    # 3. Ensure non-zero duration on all hit particle events
    patched_moves = []
    for obj in env.objects:
        if obj.type.name == "TextAsset":
            d = obj.read()
            mname = getattr(d, "m_Name", "")
            text = getattr(d, "m_Script", "")
            if "move_" in mname and "hit" in text:
                try:
                    js = json.loads(text)
                    events = js.get("moves", {}).get("events", [])
                    modified = False
                    for ev in events:
                        if ev.get("type") == "ParticleMoveEvent":
                            if ev.get("d", 0) == 0:
                                ev["d"] = 12
                                ev["inf"] = False
                                modified = True
                    if modified:
                        d.m_Script = json.dumps(js)
                        d.save()
                        patched_moves.append(mname)
                except Exception:
                    pass

    print(f"  [+] Verified and ensured particle event durations in {len(patched_moves)} moves")

    saved_bytes = env.file.save(packer="lz4")
    TARGET_MOVES_BUNDLE.write_bytes(saved_bytes)
    print(f"  [+] Saved {TARGET_MOVES_BUNDLE} ({len(saved_bytes) / 1024 / 1024:.2f} MB, LZ4 compressed)")

    # 4. Rigorous verification of moves counts on saved bundle
    verify_env = UnityPy.load(saved_bytes)
    chromia_moves = []
    deadend_moves = []
    lifeline_moves = []
    total_moves = 0
    for obj in verify_env.objects:
        if obj.type.name == "TextAsset":
            mname = getattr(obj.read(), "m_Name", "")
            if "move_" in mname:
                total_moves += 1
                if "chromia" in mname.lower():
                    chromia_moves.append(mname)
                elif "deadend" in mname.lower():
                    deadend_moves.append(mname)
                elif "lifeline" in mname.lower():
                    lifeline_moves.append(mname)

    print(f"  [+] Verification: Total={total_moves}, Chromia={len(chromia_moves)}, DeadEnd={len(deadend_moves)}, Lifeline={len(lifeline_moves)}")
    if len(chromia_moves) < 12:
        raise RuntimeError(f"FATAL: Expected at least 12 Chromia moves, found {len(chromia_moves)}!")
    if len(deadend_moves) < 8:
        raise RuntimeError(f"FATAL: Expected at least 8 DeadEnd moves, found {len(deadend_moves)}!")
    if len(lifeline_moves) < 2:
        raise RuntimeError(f"FATAL: Expected at least 2 Lifeline moves, found {len(lifeline_moves)}!")
    if total_moves < 945:
        raise RuntimeError(f"FATAL: Expected at least 945 total moves, found {total_moves}!")


def main():
    parser = argparse.ArgumentParser(description="Apply calibrated physical hit sparks to TFTF bundles")
    parser.add_argument("--preset", type=str, default="forge_ios", choices=["forge_ios", "grind_gold", "heavy_lava", "old_redeco"],
                        help="Choose a pre-defined preset")
    parser.add_argument("--speed", type=float, default=None, help="Initial spark speed (default 42.0 for forge_ios)")
    parser.add_argument("--gravity", type=float, default=None, help="Gravity scale (default 2.8 for forge_ios)")
    parser.add_argument("--length-scale", type=float, default=None, help="Length stretch scale (default -0.45)")
    parser.add_argument("--burst", type=int, default=None, help="Burst particle count (default 65)")
    parser.add_argument("--color", type=float, nargs=3, default=None, metavar=('R', 'G', 'B'),
                        help="Emissive color RGB (default: 1.0 0.38 0.08)")
    parser.add_argument("--shape", type=str, default=None, choices=["cone", "wide_cone", "sphere"],
                        help="Emitter shape")
    args = parser.parse_args()

    presets = {
        "forge_ios": {"speed": 28.0, "gravity": 16.0, "length_scale": -0.40, "burst": 110, "color": (1.0, 0.16, 0.01), "shape": "cone"},
        "grind_gold": {"speed": 24.0, "gravity": 6.5, "length_scale": -0.50, "burst": 70, "color": (1.0, 0.60, 0.08), "shape": "cone"},
        "heavy_lava": {"speed": 26.0, "gravity": 18.0, "length_scale": -0.40, "burst": 120, "color": (1.0, 0.12, 0.01), "shape": "cone"},
        "old_redeco": {"speed": 180.0, "gravity": 0.2, "length_scale": -2.2, "burst": 140, "color": (0.95, 0.84, 0.55), "shape": "sphere"},
    }

    base = presets[args.preset]
    speed = args.speed if args.speed is not None else base["speed"]
    gravity = args.gravity if args.gravity is not None else base["gravity"]
    length_scale = args.length_scale if args.length_scale is not None else base["length_scale"]
    burst = args.burst if args.burst is not None else base["burst"]
    color = tuple(args.color) if args.color is not None else base["color"]
    shape = args.shape if args.shape is not None else base["shape"]

    print("==================================================")
    print(f"🔥 TFTF Hit Sparks Calibrator - Applying Settings")
    print(f"   Active Preset: {args.preset}")
    print("==================================================")

    patch_character_fx(speed, gravity, length_scale, burst, color[0], color[1], color[2], shape)
    patch_character_fx_procedural(color[0], color[1], color[2])
    patch_moves()

    print("\n🎉 [SUCCESS] Spark parameters applied successfully to assets_redeco!")
    print("   Next: Run 'python build_apk.py' to produce test APK.")


if __name__ == "__main__":
    main()
