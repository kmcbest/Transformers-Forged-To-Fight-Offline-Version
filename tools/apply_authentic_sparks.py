#!/usr/bin/env python3
"""
tools/apply_authentic_sparks.py

Calibrates high-density physical hit sparks with authentic multi-colored materials:
1. Dense 110-burst physical spark ejection with downward gravity (16.0) and stretched streak trail (2.5).
2. Preserves authentic multi-colored spark materials (cyan block, gold crit, pink/white impact)
   instead of forcing a flat mono-color orange.
3. Preserves Netflix Chromia & Dead End SP3 assets in character_fx_procedural.
"""

import sys
import copy
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
    print("Error: UnityPy is required: pip install UnityPy lz4")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
REDECO_DIR = ROOT / "assets_redeco"
TARGET_FX_BUNDLE = REDECO_DIR / "character_fx.assetbundle"
TARGET_PROC_BUNDLE = REDECO_DIR / "character_fx_procedural.assetbundle"
BASE_APK_FX = ROOT / "extracted_apk" / "assets" / "assetpack" / "characters" / "character_fx.assetbundle"
BASE_APK_PROC = ROOT / "extracted_apk" / "assets" / "assetpack" / "characters_fx_procedural_odr" / "character_fx_procedural.assetbundle"
NETFLIX_PROC = ROOT / "assets_netflix" / "character_fx_procedural.assetbundle"


def calibrate_character_fx(speed: float = 35.0, gravity: float = 0.5, length_scale: float = 1.6, burst: int = 35):
    print(f"\n>>> Calibrating character_fx.assetbundle physics sparks:")
    print(f"    Speed={speed}, Gravity={gravity}, LengthScale={length_scale}, Burst={burst}")
    
    assert BASE_APK_FX.exists(), f"Missing base APK bundle: {BASE_APK_FX}"
    raw_data = BASE_APK_FX.read_bytes()
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
                init["maxNumParticles"] = max(init.get("maxNumParticles", 40), 1000)

                # Set StartSpeed (physics ejection)
                spd = init.get("startSpeed", {})
                if isinstance(spd, dict):
                    spd["scalar"] = float(speed)
                    if "minScalar" in spd:
                        spd["minScalar"] = float(speed * 0.30)

                # Set Lifetime (crisp bursts)
                life = init.get("startLifetime", {})
                if isinstance(life, dict):
                    life["scalar"] = 0.22
                    if "minScalar" in life:
                        life["minScalar"] = 0.08

                # Set GravityModifier (downward molten drop)
                grav = init.get("gravityModifier", {})
                if isinstance(grav, dict):
                    grav["scalar"] = float(gravity)
                    if "minScalar" in grav:
                        grav["minScalar"] = float(gravity)

                # Set Emitter Shape
                shape = raw.get("ShapeModule", {})
                if shape and isinstance(shape, dict):
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

    print(f"  [+] Calibrated {patched_ps} ParticleSystems and {patched_psr} Renderers.")
    saved_bytes = env.file.save(packer="lz4")
    TARGET_FX_BUNDLE.write_bytes(saved_bytes)
    print(f"  [+] Saved {TARGET_FX_BUNDLE} ({len(saved_bytes) / 1024 / 1024:.2f} MB, LZ4 compressed)")


def build_character_fx_procedural():
    print(f"\n>>> Assembling character_fx_procedural.assetbundle with authentic colors and Netflix assets...")
    assert BASE_APK_PROC.exists(), f"Missing base APK procedural bundle: {BASE_APK_PROC}"
    raw_data = BASE_APK_PROC.read_bytes()
    env = UnityPy.load(raw_data)
    sf = list(env.file.files.values())[0]

    # Extract Chromia materials and meshes from Netflix bundle
    chromia_mats = {}
    chromia_meshes = {}
    b_net_ress = b""
    if NETFLIX_PROC.exists():
        print(f"    Extracting Chromia assets from: {NETFLIX_PROC}")
        env_net = UnityPy.load(NETFLIX_PROC.read_bytes())
        ress_net = env_net.file.files.get("CAB-7b4e49a3d1aa1dc7f57cab96e5d8d1f7.resS")
        if ress_net:
            b_net_ress = bytes(ress_net.view) if hasattr(ress_net, "view") else ress_net.read()

        target_mesh_pids = {4547667473076947885, -8468514086234420794, 5070877881822408183}
        for obj in env_net.objects:
            if obj.type.name == "Material":
                tree = obj.read_typetree()
                if "chromia" in tree.get("m_Name", "").lower():
                    chromia_mats[obj.path_id] = tree
            elif obj.type.name == "Mesh" and (obj.path_id in target_mesh_pids or "slashmesh" in getattr(obj.read(), "m_Name", "").lower()):
                tree = obj.read_typetree()
                chromia_meshes[obj.path_id] = tree

    # Transcode 2021 Chromia materials into 2020 Material schema
    if chromia_mats:
        template_mat_reader = next((obj for obj in env.objects if obj.type.name == "Material"), None)
        assert template_mat_reader is not None
        template_mat_dict = template_mat_reader.read_typetree()
        for pid, tree_2021 in chromia_mats.items():
            new_reader = copy.copy(template_mat_reader)
            new_reader.path_id = pid
            mat_2020 = copy.deepcopy(template_mat_dict)
            mat_2020["m_Name"] = tree_2021["m_Name"]
            mat_2020["m_Shader"] = tree_2021["m_Shader"]
            mat_2020["m_SavedProperties"] = tree_2021["m_SavedProperties"]
            mat_2020["m_CustomRenderQueue"] = tree_2021.get("m_CustomRenderQueue", -1)
            mat_2020["stringTagMap"] = tree_2021.get("stringTagMap", [])
            mat_2020["disabledShaderPasses"] = tree_2021.get("disabledShaderPasses", [])
            keywords = tree_2021.get("m_ValidKeywords", [])
            mat_2020["m_ShaderKeywords"] = " ".join(keywords) if isinstance(keywords, list) else str(keywords)
            new_reader.save_typetree(mat_2020)
            sf.objects[pid] = new_reader

    # Inlining Chromia meshes
    if chromia_meshes and b_net_ress:
        template_mesh_reader = next((obj for obj in env.objects if obj.type.name == "Mesh"), None)
        assert template_mesh_reader is not None
        for pid, m_tree in chromia_meshes.items():
            sd = m_tree.get("m_StreamData", {})
            size = sd.get("size", 0)
            offset = sd.get("offset", 0)
            if size > 0 and b_net_ress:
                vbytes = b_net_ress[offset : offset + size]
                m_tree["m_VertexData"]["m_DataSize"] = vbytes
                m_tree["m_StreamData"] = {"offset": 0, "size": 0, "path": ""}
            new_m_reader = copy.copy(template_mesh_reader)
            new_m_reader.path_id = pid
            new_m_reader.save_typetree(m_tree)
            sf.objects[pid] = new_m_reader

    # Register in container
    for obj in env.objects:
        if obj.type.name == "AssetBundle":
            ab_tree = obj.read_typetree()
            container = ab_tree.get("m_Container", [])
            existing_pids = {entry[1]["asset"]["m_PathID"] for entry in container}
            for pid, tree_2021 in chromia_mats.items():
                if pid not in existing_pids:
                    container.append((f"assets/bundles/characters/materials/{tree_2021.get('m_Name').lower()}.mat",
                                      {"preloadIndex": 0, "preloadSize": 0, "asset": {"m_FileID": 0, "m_PathID": pid}}))
            for pid, m_tree in chromia_meshes.items():
                if pid not in existing_pids:
                    container.append((f"assets/bundles/characters_fx/meshes/{m_tree.get('m_Name').lower()}.asset",
                                      {"preloadIndex": 0, "preloadSize": 0, "asset": {"m_FileID": 0, "m_PathID": pid}}))
            ab_tree["m_Container"] = container
            obj.save_typetree(ab_tree)

    print("    Authentic multi-colored spark materials preserved (no single-color overwrite).")
    saved_bytes = env.file.save(packer="lz4")
    TARGET_PROC_BUNDLE.write_bytes(saved_bytes)
    print(f"  [+] Saved {TARGET_PROC_BUNDLE} ({len(saved_bytes) / 1024 / 1024:.2f} MB, LZ4 compressed)")


if __name__ == "__main__":
    calibrate_character_fx(speed=35.0, gravity=0.5, length_scale=1.6, burst=35)
    build_character_fx_procedural()
    print("\n[SUCCESS] Bundles calibrated successfully!")
