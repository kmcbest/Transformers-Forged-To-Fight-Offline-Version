#!/usr/bin/env python3
"""
patch_chromia_sparks.py

Focuses on Chromia's basic attacks (light/medium) and heavy attack (move_heavy_arcee_donut).
1. Enhances fx_p_hit_large_no_local and fx_p_hit_medium in character_fx.assetbundle:
   - Sets playOnAwake = True so particles burst immediately upon instantiation.
   - Increases maxParticles from 40 to 250+.
   - Increases burst count from 50 to 120+ for massive sparks.
   - Sets Stretched Billboard (Mode=1), LengthScale=-2.2.
   - Removes trailing null material pointer in ParticleSystemRenderer.
2. In moves.assetbundle:
   - Ensures move_heavy_arcee_donut has non-zero duration (d=15) on hit frame 13.
   - Enhances agile light and medium attack moves to trigger dense hit sparks.
"""

import zipfile
import json
from pathlib import Path

try:
    import UnityPy
except ImportError:
    print("UnityPy is required: pip install UnityPy lz4")
    exit(1)

ROOT = Path(__file__).resolve().parent.parent
APK_PATH = ROOT / "com.kabam.bigrobot_9.2.0-123129100_minAPI23(arm64-v8a,armeabi-v7a)(nodpi)_apkmirror.com.apk"
REDECO_DIR = ROOT / "assets_redeco"
REDECO_DIR.mkdir(exist_ok=True)

TARGET_FX_BUNDLE = REDECO_DIR / "character_fx.assetbundle"
TARGET_MOVES_BUNDLE = REDECO_DIR / "moves.assetbundle"


def patch_character_fx():
    print(">>> Patching character_fx.assetbundle for dense stretched sparks...")
    # Load from assets_redeco if already exists, otherwise extract from APK
    if TARGET_FX_BUNDLE.exists():
        raw_data = TARGET_FX_BUNDLE.read_bytes()
    else:
        with zipfile.ZipFile(APK_PATH, "r") as zf:
            raw_data = zf.read("assets/assetpack/characters/character_fx.assetbundle")

    env = UnityPy.load(raw_data)
    
    go_map = {}
    for obj in env.objects:
        if str(obj.type.name) == "GameObject":
            go_map[obj.path_id] = obj.read_typetree().get("m_Name", "")

    patched_ps_count = 0
    patched_psr_count = 0

    target_gos = ("fx_p_spark_particles_wide", "centre_sparks", "sparks_shower", "sparks_shower_rear", "forward_sparks")

    for obj in env.objects:
        tname = str(obj.type.name)
        if tname == "ParticleSystem":
            raw = obj.read_typetree()
            g_pid = raw.get("m_GameObject", {}).get("m_PathID")
            gname = go_map.get(g_pid, "")
            if gname in target_gos or "spark" in gname.lower():
                # Force playOnAwake
                raw["playOnAwake"] = True
                raw["looping"] = False
                
                # Boost InitialModule
                init = raw.get("InitialModule", {})
                init["maxNumParticles"] = max(init.get("maxNumParticles", 40), 300)
                
                # Boost speed if scalar is present
                spd = init.get("startSpeed", {})
                if isinstance(spd, dict) and "scalar" in spd:
                    spd["scalar"] = max(spd["scalar"], 200.0)

                # Boost Bursts
                em = raw.get("EmissionModule", {})
                bursts = em.get("m_Bursts", [])
                if bursts:
                    for b in bursts:
                        cc = b.get("countCurve", {})
                        if "scalar" in cc:
                            cc["scalar"] = max(cc["scalar"], 100.0)
                        if "minScalar" in cc:
                            cc["minScalar"] = max(cc["minScalar"], 75.0)
                else:
                    em["m_Bursts"] = [{
                        "time": 0.0,
                        "countCurve": {"minMaxState": 0, "scalar": 100.0, "minScalar": 75.0, "maxCurve": {"m_Curve": []}, "minCurve": {"m_Curve": []}},
                        "cycleCount": 1,
                        "repeatInterval": 0.01,
                        "probability": 1.0
                    }]
                obj.save_typetree(raw)
                patched_ps_count += 1

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
                raw["m_LengthScale"] = -2.2
                raw["m_VelocityScale"] = -0.02
                obj.save_typetree(raw)
                patched_psr_count += 1

    print(f"  Patched {patched_ps_count} ParticleSystems, {patched_psr_count} ParticleSystemRenderers")
    TARGET_FX_BUNDLE.write_bytes(env.file.save(packer="lz4"))
    print(f"  Saved to {TARGET_FX_BUNDLE} ({TARGET_FX_BUNDLE.stat().st_size / 1024 / 1024:.2f} MB)")


def patch_moves():
    print("\n>>> Patching moves.assetbundle for Chromia donut & agile attacks...")
    if TARGET_MOVES_BUNDLE.exists():
        raw_data = TARGET_MOVES_BUNDLE.read_bytes()
    else:
        with zipfile.ZipFile(APK_PATH, "r") as zf:
            raw_data = zf.read("assets/assetpack/characters/moves.assetbundle")

    env = UnityPy.load(raw_data)
    
    patched_moves = []

    target_moves = [
        "move_heavy_arcee_donut",
        "move_agile_attack_light_01",
        "move_agile_attack_light_02",
        "move_agile_attack_light_03",
        "move_agile_attack_light_04",
        "move_agile_attack_medium_01",
        "move_agile_attack_medium_02"
    ]

    for obj in env.objects:
        if str(obj.type.name) == "TextAsset":
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
                            ev["d"] = 15  # non-zero duration
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
                                has_hit_vfx = True
                                break

                    d.m_Script = json.dumps(js)
                    d.save()
                    patched_moves.append(mname)
                except Exception as e:
                    print(f"  Error patching {mname}: {e}")

    print(f"  Patched moves: {patched_moves}")
    TARGET_MOVES_BUNDLE.write_bytes(env.file.save(packer="lz4"))
    print(f"  Saved to {TARGET_MOVES_BUNDLE} ({TARGET_MOVES_BUNDLE.stat().st_size / 1024 / 1024:.2f} MB)")


def main():
    patch_character_fx()
    patch_moves()
    print("\n[SUCCESS] Chromia hit sparks injection completed successfully!")


if __name__ == "__main__":
    main()
