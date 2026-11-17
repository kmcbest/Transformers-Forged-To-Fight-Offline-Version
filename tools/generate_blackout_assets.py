import argparse
import copy
import sys
from pathlib import Path
import numpy as np
from PIL import Image

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

BLACKOUT_S1_CLIP_PID = 991107
BLACKOUT_S1_MOVE_PID = -8888888888888888891
BLACKOUT_FIRE_MOVE_PID = -8888888888888888893
BLACKOUT_EXPLODE_MOVE_PID = -8888888888888888894

BRIGHT_BLUE_EMISSIVE = {"r": 0.08, "g": 0.72, "b": 1.0, "a": 1.0}
BRIGHT_BLUE_TINT = {"r": 0.12, "g": 0.75, "b": 1.0}
PURPLE_FLARE_PID = 6082162931959917207
BLUE_FLARE_PID = -4339278827249707790
PARTICLE_SHADER_PID = -6819097818903621761


def replace_str_in_tree(tree_obj, old_s, new_s):
    if isinstance(tree_obj, dict):
        for k, v in list(tree_obj.items()):
            if isinstance(v, str) and old_s in v:
                tree_obj[k] = v.replace(old_s, new_s)
            else:
                replace_str_in_tree(v, old_s, new_s)
    elif isinstance(tree_obj, list):
        for idx, item in enumerate(tree_obj):
            if isinstance(item, str) and old_s in item:
                tree_obj[idx] = item.replace(old_s, new_s)
            else:
                replace_str_in_tree(item, old_s, new_s)


def commit_obj_typetree(obj, tree_data):
    if hasattr(obj, "save_typetree"):
        obj.save_typetree(tree_data)
    else:
        obj.write_typetree(tree_data)


def recolor_to_dark_gunmetal(img: Image.Image, sat_keep: float = 0.10, gamma: float = 1.25, scale: float = 0.42) -> Image.Image:
    """Recolor Grindor's pale sky-blue/white textures to Blackout's dark charcoal gunmetal grey."""
    rgba = img.convert("RGBA")
    arr = np.array(rgba, dtype=np.float32) / 255.0
    rgb = arr[:, :, :3]
    alpha = arr[:, :, 3:4]

    lum = 0.299 * rgb[:, :, 0:1] + 0.587 * rgb[:, :, 1:2] + 0.114 * rgb[:, :, 2:3]
    desat = lum + (rgb - lum) * sat_keep
    desat = np.clip(desat, 0.0, 1.0)
    dark = (np.power(desat, gamma)) * scale
    dark = np.clip(dark, 0.0, 1.0)

    out = np.concatenate([dark, alpha], axis=2)
    return Image.fromarray((out * 255.0 + 0.5).astype(np.uint8), mode="RGBA")


def recolor_fx_material_bright_blue(mat_tree: dict, is_from_cfxp: bool = False):
    """Shift purple Galvatron material properties & flare texture to bright electric blue."""
    if is_from_cfxp:
        mat_tree["m_Shader"] = {"m_FileID": 0, "m_PathID": PARTICLE_SHADER_PID}
    props = mat_tree.get("m_SavedProperties", {})
    for idx, (ck, cv) in enumerate(props.get("m_Colors", [])):
        if ck == "_emissive_intensity_col":
            props["m_Colors"][idx] = [ck, dict(BRIGHT_BLUE_EMISSIVE)]
        elif ck == "_TintColor":
            r, g, b, a = cv.get("r", 0.5), cv.get("g", 0.5), cv.get("b", 0.5), cv.get("a", 0.5)
            if abs(r - g) > 0.04 or abs(b - g) > 0.04:
                props["m_Colors"][idx] = [ck, {**BRIGHT_BLUE_TINT, "a": a}]
    for idx, (tk, tv) in enumerate(props.get("m_TexEnvs", [])):
        tex_ref = tv.get("m_Texture", {})
        tpid = int(tex_ref.get("m_PathID", 0))
        if tpid != 0:
            if is_from_cfxp and int(tex_ref.get("m_FileID", 0)) == 0:
                tex_ref["m_FileID"] = 1
            if tpid == PURPLE_FLARE_PID:
                tex_ref["m_FileID"] = 1
                tex_ref["m_PathID"] = BLUE_FLARE_PID


def trace_local_closure(sf, roots):
    """Trace all local (fid=0) objects reachable from roots without climbing m_Father."""
    visited = {}
    queue = list(roots)
    while queue:
        pid = queue.pop(0)
        if pid in visited or pid not in sf.objects:
            continue
        obj = sf.objects[pid]
        visited[pid] = obj.type.name
        if obj.type.name in ("MonoScript", "Shader", "Texture2D"):
            continue
        t = obj.read_typetree()

        def walk(node, key=""):
            if key == "m_Father":
                return
            if isinstance(node, dict):
                if "m_FileID" in node and "m_PathID" in node:
                    if int(node["m_FileID"]) == 0 and int(node["m_PathID"]) != 0:
                        rpid = int(node["m_PathID"])
                        if rpid not in visited:
                            queue.append(rpid)
                else:
                    for k, v in node.items():
                        walk(v, k)
            elif isinstance(node, list):
                for item in node:
                    walk(item, "")

        walk(t)
    return visited


def generate_blackout_assets(output_dir: str = "assets_redeco") -> None:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    preview_dir = Path("build/blackout_textures")
    preview_dir.mkdir(parents=True, exist_ok=True)

    grindor_bundle_path = Path("extracted_apk/assets/assetpack/grindor_cin_rotf_odr/grindor_cin_rotf.assetbundle")
    necro_bundle_path = Path("extracted_apk/assets/assetpack/necrotronus_gs_kabam_odr/necrotronus_gs_kabam.assetbundle")
    gal_bundle_path = Path("extracted_apk/assets/assetpack/galvatron_gs_voyager2016_odr/galvatron_gs_voyager2016.assetbundle")
    cfx_bundle_path = Path("assets_redeco/character_fx.assetbundle")
    cfxp_bundle_path = Path("assets_redeco/character_fx_procedural.assetbundle")

    print("[*] Loading source bundles...")
    g_env = UnityPy.load(str(grindor_bundle_path))
    n_env = UnityPy.load(str(necro_bundle_path))
    gal_env = UnityPy.load(str(gal_bundle_path))
    cfx_env = UnityPy.load(str(cfx_bundle_path))
    cfxp_env = UnityPy.load(str(cfxp_bundle_path))

    g_bf = list(g_env.files.values())[0]
    g_sf = list(g_env.assets)[0]
    n_sf = list(n_env.assets)[0]
    gal_sf = list(gal_env.assets)[0]
    cfx_sf = list(cfx_env.assets)[0]
    cfxp_sf = list(cfxp_env.assets)[0]

    # 1. CAB Detection & Mapping
    old_cab = "CAB-8afd6aa044e27bb02d6a7286d95293b4"
    for subfname in g_bf.files.keys():
        if subfname.startswith("CAB-") and not subfname.endswith((".resS", ".resource")):
            old_cab = subfname
            break

    new_cab = "CAB-blackout2026cin0001122334455"
    print(f"[*] Remapping CAB: {old_cab} -> {new_cab}")

    # 2. Extract & Inject Necrotronus Melee Clips + Galvatron S2 Clip
    necro_clip_specs = [
        (3678102059195295006, "Hound_Cin_attackLight_01_leftPunch", 991101, "blackout_Cin_attackLight_01_leftPunch"),
        (8504252512257503217, "brute_tantrum_attackLight_02_jab", 991102, "blackout_attackLight_02_jab"),
        (-3551880528311955755, "tactical3_normal_attacklight_01_bodyjab_L", 991103, "blackout_attacklight_01_bodyjab_L"),
        (8948850516725818086, "brute_tantrum_attackLight_04_uppcut", 991104, "blackout_attackLight_04_uppcut"),
        (7265497203347661852, "tactical3_normal_attackMedium_01_shoulder_L", 991105, "blackout_attackMedium_01_shoulder_L"),
        (-1740342661625100663, "tactical3_normal_attackMedium_02_frontkick_R", 991106, "blackout_attackMedium_02_frontkick_R"),
    ]
    n_clip_by_name = {}
    for o in n_sf.objects.values():
        if o.type.name == "AnimationClip":
            ct = o.read_typetree()
            n_clip_by_name[ct.get("m_Name", "")] = ct

    template_clip = [o for o in g_sf.objects.values() if o.type.name == "AnimationClip"][0]
    injected_pids = []

    for src_pid, src_name, dst_pid, new_name in necro_clip_specs:
        ctree = copy.deepcopy(n_sf.objects[src_pid].read_typetree() if src_pid in n_sf.objects else n_clip_by_name[src_name])
        ctree["m_Name"] = new_name
        replace_str_in_tree(ctree, old_cab, new_cab)
        new_obj = copy.copy(template_clip)
        new_obj.path_id = dst_pid
        commit_obj_typetree(new_obj, ctree)
        g_sf.objects[dst_pid] = new_obj
        injected_pids.append(dst_pid)

    # Inject Galvatron S2 AnimationClip (6942792735420182761) at 991107 for Blackout S1
    gal_s2_clip_tree = copy.deepcopy(gal_sf.objects[6942792735420182761].read_typetree())
    gal_s2_clip_tree["m_Name"] = "blackout_attackSpecial_01_galvatron"
    replace_str_in_tree(gal_s2_clip_tree, old_cab, new_cab)
    new_s1_clip = copy.copy(template_clip)
    new_s1_clip.path_id = BLACKOUT_S1_CLIP_PID
    commit_obj_typetree(new_s1_clip, gal_s2_clip_tree)
    g_sf.objects[BLACKOUT_S1_CLIP_PID] = new_s1_clip
    injected_pids.append(BLACKOUT_S1_CLIP_PID)
    print(f"[*] Injected {len(injected_pids)} clips (6 Necrotronus melee + Galvatron S2 clip -> Blackout S1).")

    # 2.5. Graft & Recolor Galvatron S2 Energy Projectile + Bright-Blue FX into Blackout bundle
    pid_counter = [-8810000000000000001]

    def alloc_pid() -> int:
        while pid_counter[0] in g_sf.objects:
            pid_counter[0] -= 1
        val = pid_counter[0]
        pid_counter[0] -= 1
        return val

    # Native templates in g_sf keyed by (type_name, script_pid_if_mb)
    g_tpl_by_type = {}
    g_mb_tpl_by_script = {}
    for o in g_sf.objects.values():
        if o.type.name == "MonoBehaviour":
            spid = int(o.read_typetree().get("m_Script", {}).get("m_PathID", 0))
            if spid not in g_mb_tpl_by_script:
                g_mb_tpl_by_script[spid] = o
        elif o.type.name not in g_tpl_by_type:
            g_tpl_by_type[o.type.name] = o

    # Clone the 5 external cfxp materials used by Galvatron FX locally so we can recolor them bright blue
    cfxp_mat_pids = [
        6875643828576203248,   # fx_m_galvatron_charge_laser_a
        8846740354647462645,   # fx_m_galvatron_lines_a
        2970504914179255923,   # fx_m_galvatron_blast_streaks_a
        -7212005930988979262,  # fx_m_galvatron_blast_charge_laser_a
        8969480828214528708,   # fx_m_galvatron_blast_charge_sparks_a
    ]
    cfxp_mat_map = {}
    grafted_pids = []
    for old_mpid in cfxp_mat_pids:
        new_mpid = alloc_pid()
        mt = copy.deepcopy(cfxp_sf.objects[old_mpid].read_typetree())
        mt["m_Name"] = mt.get("m_Name", "").replace("galvatron", "blackout")
        recolor_fx_material_bright_blue(mt, is_from_cfxp=True)
        new_mat = copy.copy(g_tpl_by_type["Material"])
        new_mat.path_id = new_mpid
        commit_obj_typetree(new_mat, mt)
        g_sf.objects[new_mpid] = new_mat
        cfxp_mat_map[old_mpid] = new_mpid
        grafted_pids.append(new_mpid)

    # Clone cfx:fx_p_galvatron_projectile_impact (-7910710858010517098) -> fx_p_blackout_projectile_impact
    cfx_impact_root = -7910710858010517098
    cfx_closure = trace_local_closure(cfx_sf, [cfx_impact_root])
    cfx_pid_map = {}
    for pid, tp in cfx_closure.items():
        if tp not in ("MonoScript", "Shader"):
            cfx_pid_map[pid] = alloc_pid()

    for old_pid, tp in cfx_closure.items():
        if tp in ("MonoScript", "Shader"):
            continue
        new_pid = cfx_pid_map[old_pid]
        tree = copy.deepcopy(cfx_sf.objects[old_pid].read_typetree())
        if old_pid == cfx_impact_root:
            tree["m_Name"] = "fx_p_blackout_projectile_impact"
        if tp == "Material":
            tree["m_Name"] = tree.get("m_Name", "").replace("galvatron", "blackout")
            recolor_fx_material_bright_blue(tree, is_from_cfxp=False)

        def remap_cfx(node):
            if isinstance(node, dict):
                if "m_FileID" in node and "m_PathID" in node:
                    fid, rpid = int(node["m_FileID"]), int(node["m_PathID"])
                    if fid == 0 and rpid in cfx_pid_map:
                        node["m_PathID"] = cfx_pid_map[rpid]
                    elif fid == 2:
                        # cfx fid=2 is Library/unity default resources -> fid=6 in Grindor
                        node["m_FileID"] = 6
                else:
                    for v in node.values():
                        remap_cfx(v)
            elif isinstance(node, list):
                for it in node:
                    remap_cfx(it)

        remap_cfx(tree)
        if tp == "MonoBehaviour":
            spid = int(tree.get("m_Script", {}).get("m_PathID", 0))
            tpl = g_mb_tpl_by_script[spid]
        else:
            tpl = g_tpl_by_type[tp]
        new_obj = copy.copy(tpl)
        new_obj.path_id = new_pid
        commit_obj_typetree(new_obj, tree)
        g_sf.objects[new_pid] = new_obj
        grafted_pids.append(new_pid)

    impact_new_pid = cfx_pid_map[cfx_impact_root]

    # Clone Galvatron S2 projectile & FX closures
    gal_root_renames = {
        7844017693230829075: "projectile_blackout_energy_bullet",
        1707416394268060215: "fx_p_blackout_large_projectile",
        -1986879546624301645: "fx_p_blackout_charge_up",
        2570907183088606735: "fx_p_blackout_energy_ball",
        7248483950455624021: "fx_p_blackout_blast_streaks",
        -6802706632167550083: "fx_p_blackout_blast_discharge",
        -7568857660993260739: "fx_p_blackout_large_blast",
    }
    gal_closure = trace_local_closure(gal_sf, list(gal_root_renames.keys()))
    gal_pid_map = {}
    for pid, tp in gal_closure.items():
        if tp not in ("MonoScript", "Shader"):
            gal_pid_map[pid] = alloc_pid()

    gal_root_tr_pids = {
        int(gal_sf.objects[rpid].read_typetree()["m_Component"][0]["component"]["m_PathID"])
        for rpid in gal_root_renames
    }

    for old_pid, tp in gal_closure.items():
        if tp in ("MonoScript", "Shader"):
            continue
        new_pid = gal_pid_map[old_pid]

        # Decode & inline streamed Texture2D (fx_t_flare_hot) cleanly
        if tp == "Texture2D":
            src_tex = gal_sf.objects[old_pid].read()
            src_img = src_tex.image.convert("RGBA")
            new_tex_obj = copy.copy(g_tpl_by_type["Texture2D"])
            new_tex_obj.path_id = new_pid
            t_inst = new_tex_obj.read()
            t_inst.m_Name = getattr(src_tex, "m_Name", "fx_t_blackout_flare_hot")
            t_inst.image = src_img
            t_inst.save()
            g_sf.objects[new_pid] = new_tex_obj
            grafted_pids.append(new_pid)
            continue

        tree = copy.deepcopy(gal_sf.objects[old_pid].read_typetree())
        if old_pid in gal_root_renames:
            tree["m_Name"] = gal_root_renames[old_pid]
        if old_pid in gal_root_tr_pids:
            tree["m_Father"] = {"m_FileID": 0, "m_PathID": 0}
        if tp == "Material":
            tree["m_Name"] = tree.get("m_Name", "").replace("galvatron", "blackout")
            recolor_fx_material_bright_blue(tree, is_from_cfxp=False)

        def remap_gal(node):
            if isinstance(node, dict):
                if "m_FileID" in node and "m_PathID" in node:
                    fid, rpid = int(node["m_FileID"]), int(node["m_PathID"])
                    if fid == 0 and rpid in gal_pid_map:
                        node["m_PathID"] = gal_pid_map[rpid]
                    elif fid == 1 and rpid in cfxp_mat_map:
                        node["m_FileID"] = 0
                        node["m_PathID"] = cfxp_mat_map[rpid]
                    elif fid == 3:
                        # Galvatron fid=3 is Library/unity default resources -> fid=6 in Grindor
                        node["m_FileID"] = 6
                    elif fid == 6:
                        # Galvatron fid=6 is character_fx -> fid=4 in Grindor
                        node["m_FileID"] = 4
                else:
                    for v in node.values():
                        remap_gal(v)
            elif isinstance(node, list):
                for it in node:
                    remap_gal(it)

        remap_gal(tree)

        if tp == "MonoBehaviour":
            spid = int(tree.get("m_Script", {}).get("m_PathID", 0))
            if spid == 2297153707519481197:  # MoveSet on projectile_blackout_energy_bullet
                for mv in tree.get("_moves", []):
                    if mv.get("_name") == "fire":
                        mv["_asset"] = {"m_FileID": 5, "m_PathID": BLACKOUT_FIRE_MOVE_PID}
                    else:
                        mv["_asset"] = {"m_FileID": 5, "m_PathID": BLACKOUT_EXPLODE_MOVE_PID}
            elif spid == -3815473324432562333:  # PrefabLib on projectile_blackout_energy_bullet
                tree["PrefabList"] = [
                    {"Prefab": {"m_FileID": 1, "m_PathID": -2054079777877699854}, "Amount": 1},  # fx_l_hit_small_blue_perceptual
                    {"Prefab": {"m_FileID": 0, "m_PathID": gal_pid_map[1707416394268060215]}, "Amount": 1},  # fx_p_blackout_large_projectile
                    {"Prefab": {"m_FileID": 0, "m_PathID": impact_new_pid}, "Amount": 1},  # fx_p_blackout_projectile_impact
                ]
            tpl = g_mb_tpl_by_script[spid]
        else:
            tpl = g_tpl_by_type[tp]

        new_obj = copy.copy(tpl)
        new_obj.path_id = new_pid
        commit_obj_typetree(new_obj, tree)
        g_sf.objects[new_pid] = new_obj
        grafted_pids.append(new_pid)

    proj_new_pid = gal_pid_map[7844017693230829075]
    print(f"[+] Grafted & recolored bright-blue Galvatron S2 FX ({len(grafted_pids)} objects, proj={proj_new_pid}).")

    # Register all S1 prefabs + shared blue trail/lights in Blackout's main PrefabLib (-5353390358171322875)
    prefablib_obj = g_sf.objects[-5353390358171322875]
    prefablib_tree = prefablib_obj.read_typetree()
    plist = prefablib_tree.get("PrefabList", [])
    existing_refs = {
        (int(p.get("Prefab", {}).get("m_FileID", 0)), int(p.get("Prefab", {}).get("m_PathID", 0)))
        for p in plist
    }
    s1_required_prefabs = [
        (0, proj_new_pid, 3),                              # projectile_blackout_energy_bullet
        (0, gal_pid_map[-1986879546624301645], 1),         # fx_p_blackout_charge_up
        (0, gal_pid_map[2570907183088606735], 1),          # fx_p_blackout_energy_ball
        (0, gal_pid_map[7248483950455624021], 1),          # fx_p_blackout_blast_streaks
        (0, gal_pid_map[-6802706632167550083], 1),         # fx_p_blackout_blast_discharge
        (0, gal_pid_map[-7568857660993260739], 1),         # fx_p_blackout_large_blast
        (4, 3383258741578490413, 2),                       # fx_r_trail_optimus_gs (bright blue trail)
        (4, 5846517154461878008, 1),                       # fx_p_hit_large_lite
        (4, -1685458833540413680, 1),                      # fx_p_hit_punch_sparks_special
        (1, -1981576416574566773, 1),                      # fx_l_hit_special_perceptual
        (1, -2054079777877699854, 1),                      # fx_l_hit_small_blue_perceptual
    ]
    for fid, pid, amt in s1_required_prefabs:
        if (fid, pid) not in existing_refs:
            plist.append({"Prefab": {"m_FileID": fid, "m_PathID": pid}, "Amount": amt})
            existing_refs.add((fid, pid))
    prefablib_tree["PrefabList"] = plist
    commit_obj_typetree(prefablib_obj, prefablib_tree)
    print(f"[+] Updated Blackout main PrefabLib ({len(plist)} items).")

    # 3. Configure Fight AOC (PID 259380691726149969)
    aoc_obj = g_sf.objects[259380691726149969]
    aoc_tree = aoc_obj.read_typetree()
    clips = aoc_tree.get("m_Clips", [])

    clips[2]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": 991101}
    clips[3]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": 991102}
    clips[41]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": 991103}
    clips[43]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": 991104}
    clips[42]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": 991105}
    clips[44]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": 991106}

    # Slot 58 (char_attackHeavy) -> Grindor native heavy missile fire
    clips[58]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": -7224602046215420873}

    # Specials:
    # Slot 4: S1 -> Galvatron S2 clip (991107)
    clips[4]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": BLACKOUT_S1_CLIP_PID}
    # Slot 5: S2 -> Grindor native S2 restored!
    clips[5]["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": 5129418086538677414}

    # Victory:
    clips[39]["m_OverrideClip"] = {"m_FileID": 2, "m_PathID": -7535929919115318753}
    clips[40]["m_OverrideClip"] = {"m_FileID": 2, "m_PathID": -4195553960651922483}

    aoc_tree["m_Clips"] = clips
    replace_str_in_tree(aoc_tree, old_cab, new_cab)
    commit_obj_typetree(aoc_obj, aoc_tree)
    print("[+] Configured Fight AOC (S1=Galvatron S2, S2=Grindor Native S2, Melee=Necrotronus)!")

    # 4. Configure MoveSet (PID -2282744758651308026)
    ms_obj = g_sf.objects[-2282744758651308026]
    ms_tree = ms_obj.read_typetree()
    moves = ms_tree["_moves"]

    moves[0]["_name"] = "move_megatronus_attack_light_01"
    moves[0]["_asset"] = {"m_FileID": 5, "m_PathID": -6740464737614209425}
    moves[1]["_name"] = "move_megatronus_attack_light_02"
    moves[1]["_asset"] = {"m_FileID": 5, "m_PathID": 2095223796171100125}
    moves[2]["_name"] = "move_megatronus_attack_light_03"
    moves[2]["_asset"] = {"m_FileID": 5, "m_PathID": 6374914769425836133}
    moves[3]["_name"] = "move_megatronus_attack_light_04"
    moves[3]["_asset"] = {"m_FileID": 5, "m_PathID": 8656719042657693179}
    moves[4]["_name"] = "move_megatronus_attack_medium_01"
    moves[4]["_asset"] = {"m_FileID": 5, "m_PathID": 3267735181318500007}
    moves[5]["_name"] = "move_megatronus_attack_medium_02"
    moves[5]["_asset"] = {"m_FileID": 5, "m_PathID": 5104354136730126689}

    # S1: move_blackout_special_01 (Galvatron S2 w/ bright blue energy projectile)
    moves[6]["_name"] = "move_blackout_special_01"
    moves[6]["_asset"] = {"m_FileID": 5, "m_PathID": BLACKOUT_S1_MOVE_PID}

    # S2: Grindor native S2 restored!
    moves[7]["_name"] = "move_grindor_special_02"
    moves[7]["_asset"] = {"m_FileID": 5, "m_PathID": 4021532362125562773}

    moves[44]["_name"] = "move_heavy_plane_shoot"
    moves[44]["_asset"] = {"m_FileID": 5, "m_PathID": -7784374527050455307}

    ms_tree["_moves"] = moves
    replace_str_in_tree(ms_tree, old_cab, new_cab)
    commit_obj_typetree(ms_obj, ms_tree)
    print("[+] Configured MoveSet (_moves[6]=move_blackout_special_01, _moves[7]=move_grindor_special_02)!")

    # 5. Configure PlayerReferences Victory Stage (PID 4809715625580256617)
    pref_obj = g_sf.objects[4809715625580256617]
    pref_tree = pref_obj.read_typetree()
    pref_tree["VictoryStagePrefab"] = {"m_FileID": 7, "m_PathID": 7184980468553159185}
    replace_str_in_tree(pref_tree, old_cab, new_cab)
    commit_obj_typetree(pref_obj, pref_tree)

    # 6. Recolor & Inject Dark Gunmetal Grey Textures (skip newly grafted FX textures!)
    grafted_set = set(grafted_pids)
    recolor_targets = {"cha_grindor_cin_rotf_main_a", "tform_misc_A", "cha_grindor_cin_rotf_wpns_a"}
    for pid, obj in list(g_sf.objects.items()):
        if pid in grafted_set:
            continue
        if obj.type.name == "Texture2D":
            tex_name = obj.read_typetree().get("m_Name", "")
            if tex_name in recolor_targets:
                tex = obj.read()
                orig_img = tex.image
                dark_img = recolor_to_dark_gunmetal(orig_img, sat_keep=0.10, gamma=1.25, scale=0.42)
                dark_img.save(preview_dir / f"blackout_{tex_name}.png")
                tex.image = dark_img
                tex.save()
                arr = np.array(dark_img, dtype=np.float32)[:, :, :3]
                print(f"[+] Recolored {tex_name} -> dark gunmetal (mean RGB={arr.mean(axis=(0,1)).round(1).tolist()})")
            else:
                tree = obj.read_typetree()
                replace_str_in_tree(tree, old_cab, new_cab)
                commit_obj_typetree(obj, tree)

    # 7. AssetBundle object: update container and preload table
    for obj in g_sf.objects.values():
        if obj.type.name == "AssetBundle":
            tree = obj.read_typetree()
            tree["m_Name"] = "data/blackout_cin_tf_odr/blackout_cin_tf.assetbundle"
            container = tree.get("m_Container", [])
            new_container = []
            for item in container:
                path_str = item[0].replace("grindor_cin_rotf", "blackout_cin_tf").replace("rotf", "tf")
                new_container.append([path_str, item[1]])
            tree["m_Container"] = new_container

            preload = tree.get("m_PreloadTable", [])
            existing_preload = {(p.get("m_FileID", 0), p.get("m_PathID", 0)) for p in preload}
            extra_preload = (
                [(0, ipid) for ipid in injected_pids]
                + [(0, gpid) for gpid in grafted_pids]
                + [
                    (4, 3383258741578490413),
                    (4, 5846517154461878008),
                    (4, -1685458833540413680),
                    (1, -1981576416574566773),
                    (1, -2054079777877699854),
                    (1, BLUE_FLARE_PID),
                    (1, 3731911469176567051),
                    (1, -4392597687826872290),
                    (1, -4772189363306452888),
                    (1, -7184898897910996630),
                    (1, -1464506978602793161),
                    (1, -8779232328077929462),
                    (1, -4117005291785525941),
                    (1, -4304287316655623132),
                    (1, -3408802541521723336),
                    (1, 2418718117538121018),
                    (1, 4111907626491324471),
                    (1, 7643310754666517133),
                ]
            )
            for fid, pid in extra_preload:
                if (fid, pid) not in existing_preload:
                    preload.append({"m_FileID": fid, "m_PathID": pid})
                    existing_preload.add((fid, pid))
            tree["m_PreloadTable"] = preload

            replace_str_in_tree(tree, old_cab, new_cab)
            commit_obj_typetree(obj, tree)
            print(f"[+] Updated AssetBundle container and preload list ({len(preload)} items)!")

    # 8. Deep CAB isolation across all objects (skipping already processed/committed objects)
    skip_pids = {
        259380691726149969,   # Fight AOC
        -2282744758651308026, # MoveSet
        -5353390358171322875, # PrefabLib
        4809715625580256617,  # PlayerReferences
    } | set(injected_pids) | grafted_set

    for pid, obj in g_sf.objects.items():
        if pid in skip_pids:
            continue
        if obj.type.name not in ["Texture2D", "AssetBundle"]:
            try:
                tree = obj.read_typetree()
                replace_str_in_tree(tree, old_cab, new_cab)
                commit_obj_typetree(obj, tree)
            except Exception:
                pass

    # 9. Chapter 9 Quality Gate: Sort script_types ascending
    skeys = [(s.local_serialized_file_index, s.local_identifier_in_file) for s in g_sf.script_types]
    if skeys != sorted(skeys):
        print("[*] Sorting g_sf.script_types ascending...")
        old_to_new_sidx = {}
        sorted_script_types = sorted(
            enumerate(g_sf.script_types),
            key=lambda x: (x[1].local_serialized_file_index, x[1].local_identifier_in_file)
        )
        new_list = []
        for new_idx, (old_idx, sref) in enumerate(sorted_script_types):
            old_to_new_sidx[old_idx] = new_idx
            new_list.append(sref)
        g_sf.script_types = new_list
        for tp in g_sf.types:
            if tp.script_type_index >= 0:
                tp.script_type_index = old_to_new_sidx.get(tp.script_type_index, tp.script_type_index)

    # 10. Save rebuilt AssetBundle
    new_files = {}
    for subfname, subf in g_bf.files.items():
        new_subfname = subfname.replace(old_cab, new_cab)
        if hasattr(subf, "name"):
            subf.name = new_subfname
        new_files[new_subfname] = subf

    g_bf.files = new_files
    g_bf.version = 7
    g_bf.version_engine = "2020.3.31f1"
    g_bf.version_player = "5.x.x"

    target_bundle = out_dir / "blackout_cin_tf.assetbundle"
    target_bundle.write_bytes(g_bf.save(packer="lz4"))
    print(f"[+] Rebuilt UnityFS AssetBundle -> {target_bundle} ({target_bundle.stat().st_size:,} bytes)")
    print("[+] Blackout assetbundle generation complete!")


def main():
    parser = argparse.ArgumentParser(description="Generate Blackout (眩晕) composite assets.")
    parser.add_argument("--output", "-o", default="assets_redeco", help="Output directory")
    args = parser.parse_args()
    generate_blackout_assets(output_dir=args.output)


if __name__ == "__main__":
    main()
