import copy
import io
import json
import os
import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

BLACKOUT_BUNDLE_PATH = Path("assets_redeco/blackout_cin_tf.assetbundle")
MOVES_BUNDLE_PATH = Path("assets_redeco/moves.assetbundle")
SCORP_BUNDLE_PATH = Path("extracted_apk/assets/assetpack/scorponok_bw_kabam_odr/scorponok_bw_kabam.assetbundle")
JETFIRE_BUNDLE_PATH = Path("extracted_apk/assets/assetpack/jetfire_gs_leader2014_odr/jetfire_gs_leader2014.assetbundle")
NETFLIX_MOVES_PATH = Path("assets_netflix/moves.assetbundle")

BLACKOUT_S1_CLIP_PID = 991107
BLACKOUT_S1_MOVE_PID = -8888888888888888891
SCORP_S1_CLIP_PID = 2089475156797672158
SCORP_S1_MOVE_PID = 4986668334192263653
SCORP_AUDIO_PID = -6289018736068080735

JETFIRE_BULLET_ROOT_PID = -4974897630503332193   # projectile_jetfire_sp1_bullet
JETFIRE_FX_PROJ_PID = 2901470354927815027         # fx_p_jetfire_special_projectile
JETFIRE_FX_IMPACT_PID = -2859918092256556932      # fx_p_jetfire_projectile_impact
JETFIRE_LOCAL_TEX_PID = -409150583701915127        # fx_t_LaserBeamFlare

PARTICLE_SHADER_PID = -6819097818903621761
MAIN_PREFABLIB_PID = -5353390358171322875

# Map external FileIDs from Jetfire bundle to Blackout bundle
JETFIRE_TO_BLACKOUT_FILEID_MAP = {
    1: 1,  # CAB-7b4e49a3d1aa1dc7f57cab96e5d8d1f7 (cfxp base)
    2: 2,  # CAB-48a8fb7c73226df35ecf6a5823f21dd6 (shared fx)
    3: 5,  # CAB-47012f9f52e0ee1cac4dfad2d29a972d (moves.assetbundle! Crucial for bullet MoveSet!)
    4: 6,  # unity default resources (Mesh 10207 Sphere! Crucial for energy ball mesh!)
    5: 4,  # CAB-a742a3fff84aa604ba32daca2b1ea500 (cfxp add)
    6: 3,  # CAB-de7c749530a5ce51ab49ae7f3bcf1777
    8: 7,  # CAB-ab43fd15c150476227e8346a96b20ca7
}

def trace_closure(sf, root_pids):
    visited = set()
    queue = list(root_pids)
    closure = {}
    while queue:
        pid = queue.pop(0)
        if pid in visited:
            continue
        visited.add(pid)
        if pid not in sf.objects:
            continue
        obj = sf.objects[pid]
        closure[pid] = obj.type.name
        try:
            tree = obj.read_typetree()
            def find_pids(node):
                if isinstance(node, dict):
                    if "m_FileID" in node and "m_PathID" in node:
                        fid, p = int(node["m_FileID"]), int(node["m_PathID"])
                        if fid == 0 and p != 0 and p not in visited:
                            queue.append(p)
                    for v in node.values():
                        find_pids(v)
                elif isinstance(node, list):
                    for it in node:
                        find_pids(it)
            find_pids(tree)
        except Exception:
            pass
    return closure

def commit_obj_typetree(obj, tree):
    if hasattr(obj, "save_typetree"):
        obj.save_typetree(tree)
    elif hasattr(obj, "write_typetree"):
        obj.write_typetree(tree)
    else:
        raise AttributeError("Object has no save_typetree or write_typetree method")

def patch_blackout_bundle():
    print("[1/4] Loading bundles for Blackout character patch...")
    env_b = UnityPy.load(str(BLACKOUT_BUNDLE_PATH))
    bf_b = list(env_b.files.values())[0]
    sf_b = list(env_b.assets)[0]

    env_s = UnityPy.load(str(SCORP_BUNDLE_PATH))
    bf_s = list(env_s.files.values())[0]
    sf_s = list(env_s.assets)[0]

    env_j = UnityPy.load(str(JETFIRE_BUNDLE_PATH))
    sf_j = list(env_j.assets)[0]

    # -------------------------------------------------------------
    # 1. Action Animation: Scorponok S1 Clip -> Blackout S1 Clip
    # -------------------------------------------------------------
    print("[2/4] Grafting Scorponok S1 animation into Blackout bundle...")
    scorp_clip_obj = sf_s.objects[SCORP_S1_CLIP_PID]
    scorp_clip_tree = copy.deepcopy(scorp_clip_obj.read_typetree())
    scorp_clip_tree["m_Name"] = "blackout_attackSpecial_01_scorponok"

    # Replace old S1 clip (PID 991107) in blackout bundle
    s1_clip_obj = sf_b.objects[BLACKOUT_S1_CLIP_PID]
    commit_obj_typetree(s1_clip_obj, scorp_clip_tree)
    print(f"  [+] Overwrote AnimationClip {BLACKOUT_S1_CLIP_PID} with Scorponok S1 animation (len={scorp_clip_tree['m_MuscleClip']['m_StopTime']}s)")

    # -------------------------------------------------------------
    # 2. Audio: Scorponok S1 Sound -> Blackout grindor_special_1
    # -------------------------------------------------------------
    print("[3/4] Grafting Scorponok S1 audio into Blackout bundle...")
    scorp_audio_obj = sf_s.objects[SCORP_AUDIO_PID]
    scorp_audio_tree = copy.deepcopy(scorp_audio_obj.read_typetree())

    # Extract audio bytes from Scorponok's .resource file
    scorp_res_name = None
    for fn in bf_s.files.keys():
        if fn.endswith(".resource"):
            scorp_res_name = fn
            break
    assert scorp_res_name, "Cannot find .resource in Scorponok bundle"
    scorp_res_stream = bf_s.files[scorp_res_name]
    scorp_res_bytes = bytes(scorp_res_stream.read() if hasattr(scorp_res_stream, "read") else scorp_res_stream.bytes)
    audio_offset = scorp_audio_tree["m_Resource"]["m_Offset"]
    audio_size = scorp_audio_tree["m_Resource"]["m_Size"]
    scorp_sound_data = scorp_res_bytes[audio_offset:audio_offset + audio_size]
    print(f"  [+] Extracted Scorponok S1 audio data: {len(scorp_sound_data)} bytes (offset={audio_offset}, size={audio_size})")

    # Append to Blackout's .resource file
    blackout_res_name = None
    for fn in bf_b.files.keys():
        if fn.endswith(".resource"):
            blackout_res_name = fn
            break
    assert blackout_res_name, "Cannot find .resource in Blackout bundle"
    blackout_res_stream = bf_b.files[blackout_res_name]
    orig_b_bytes = bytes(blackout_res_stream.read() if hasattr(blackout_res_stream, "read") else blackout_res_stream.bytes)
    new_offset = len(orig_b_bytes)
    # Align to 16 bytes
    if new_offset % 16 != 0:
        orig_b_bytes += b'\x00' * (16 - (new_offset % 16))
        new_offset = len(orig_b_bytes)

    new_b_bytes = orig_b_bytes + scorp_sound_data
    from UnityPy.streams import EndianBinaryReader
    new_reader = EndianBinaryReader(new_b_bytes)
    new_reader.flags = 0
    bf_b.files[blackout_res_name] = new_reader
    print(f"  [+] Appended sound data to {blackout_res_name}: new_offset={new_offset}, total_len={len(new_b_bytes)}")

    # Update grindor_special_1 AudioClip
    grindor_sp1_obj = None
    for o in sf_b.objects.values():
        if o.type.name == "AudioClip" and o.read_typetree().get("m_Name") == "grindor_special_1":
            grindor_sp1_obj = o
            break
    assert grindor_sp1_obj, "Cannot find grindor_special_1 AudioClip in Blackout bundle"

    grindor_audio_tree = grindor_sp1_obj.read_typetree()
    for prop in ["m_LoadType", "m_Channels", "m_Frequency", "m_BitsPerSample", "m_Length",
                 "m_IsTrackerFormat", "m_Ambisonic", "m_SubsoundIndex", "m_PreloadAudioData",
                 "m_LoadInBackground", "m_Legacy3D", "m_CompressionFormat"]:
        if prop in scorp_audio_tree:
            grindor_audio_tree[prop] = scorp_audio_tree[prop]
    grindor_audio_tree["m_Resource"]["m_Offset"] = new_offset
    grindor_audio_tree["m_Resource"]["m_Size"] = audio_size
    commit_obj_typetree(grindor_sp1_obj, grindor_audio_tree)
    print(f"  [+] Updated grindor_special_1 AudioClip (offset={new_offset}, len={grindor_audio_tree['m_Length']}s)")

    # -------------------------------------------------------------
    # 3. Projectile: Graft Jetfire S1 Projectile & FX into Blackout
    # -------------------------------------------------------------
    print("[4/4] Grafting Jetfire S1 Projectile & FX closure into Blackout bundle...")
    roots = [JETFIRE_BULLET_ROOT_PID, JETFIRE_FX_PROJ_PID, JETFIRE_FX_IMPACT_PID]
    closure = trace_closure(sf_j, roots)
    print(f"  [+] Traced Jetfire closure: {len(closure)} objects")

    pid_counter = [-8820000000000000001]
    def alloc_pid():
        while pid_counter[0] in sf_b.objects:
            pid_counter[0] -= 1
        val = pid_counter[0]
        pid_counter[0] -= 1
        return val

    # Template objects in sf_b by type and MonoBehaviour script
    b_tpl_by_type = {}
    b_mb_by_script = {}
    for o in sf_b.objects.values():
        if o.type.name == "MonoBehaviour":
            spid = int(o.read_typetree().get("m_Script", {}).get("m_PathID", 0))
            if spid not in b_mb_by_script:
                b_mb_by_script[spid] = o
        elif o.type.name not in b_tpl_by_type:
            b_tpl_by_type[o.type.name] = o

    # Decode and inline local texture fx_t_LaserBeamFlare (-409150583701915127)
    new_tex_pid = alloc_pid()
    src_tex = sf_j.objects[JETFIRE_LOCAL_TEX_PID].read()
    src_img = src_tex.image.convert("RGBA")
    new_tex_obj = copy.copy(b_tpl_by_type["Texture2D"])
    new_tex_obj.path_id = new_tex_pid
    t_inst = new_tex_obj.read()
    t_inst.m_Name = "fx_t_LaserBeamFlare"
    t_inst.image = src_img
    t_inst.save()
    sf_b.objects[new_tex_pid] = new_tex_obj
    print(f"  [+] Inlined Texture2D fx_t_LaserBeamFlare (PID {new_tex_pid}, size={src_img.size})")

    pid_map = {}
    for pid, tname in closure.items():
        if tname not in ("MonoScript", "Shader"):
            pid_map[pid] = alloc_pid()

    # Re-map Typetrees and inject
    injected_roots = {}
    for old_pid, tname in closure.items():
        if tname in ("MonoScript", "Shader"):
            continue
        new_pid = pid_map[old_pid]
        tree = copy.deepcopy(sf_j.objects[old_pid].read_typetree())

        # Remap internal pointers and external FileIDs
        def remap_pointers(node):
            if isinstance(node, dict):
                if "m_FileID" in node and "m_PathID" in node:
                    fid, rpid = int(node["m_FileID"]), int(node["m_PathID"])
                    if fid == 0:
                        if rpid in pid_map:
                            node["m_PathID"] = pid_map[rpid]
                        elif rpid == PARTICLE_SHADER_PID:
                            node["m_PathID"] = PARTICLE_SHADER_PID
                        elif rpid == JETFIRE_LOCAL_TEX_PID:
                            node["m_PathID"] = new_tex_pid
                    elif fid > 0 and fid in JETFIRE_TO_BLACKOUT_FILEID_MAP:
                        node["m_FileID"] = JETFIRE_TO_BLACKOUT_FILEID_MAP[fid]
                else:
                    for v in node.values():
                        remap_pointers(v)
            elif isinstance(node, (list, tuple)):
                for item in node:
                    remap_pointers(item)

        remap_pointers(tree)

        # For Material, ensure Shader points to Particle Shader and texture refs are fixed
        if tname == "Material":
            tree["m_Shader"] = {"m_FileID": 0, "m_PathID": PARTICLE_SHADER_PID}
            props = tree.get("m_SavedProperties", {})
            for tex_pair in props.get("m_TexEnvs", []):
                tprop, tenv = tex_pair[0], tex_pair[1]
                tref = tenv.get("m_Texture", {})
                fid = int(tref.get("m_FileID", 0))
                pid = int(tref.get("m_PathID", 0))
                if fid == 0 and pid == JETFIRE_LOCAL_TEX_PID:
                    tref["m_PathID"] = new_tex_pid
                elif fid > 0 and fid in JETFIRE_TO_BLACKOUT_FILEID_MAP:
                    tref["m_FileID"] = JETFIRE_TO_BLACKOUT_FILEID_MAP[fid]

        # For root GameObjects, ensure Transform m_Father is 0
        if old_pid in roots and tname == "GameObject":
            injected_roots[tree.get("m_Name")] = new_pid

        if tname == "MonoBehaviour":
            spid = int(tree.get("m_Script", {}).get("m_PathID", 0))
            tpl = b_mb_by_script[spid]
        else:
            tpl = b_tpl_by_type[tname]

        new_obj = copy.copy(tpl)
        new_obj.path_id = new_pid
        commit_obj_typetree(new_obj, tree)
        sf_b.objects[new_pid] = new_obj

    print(f"  [+] Injected {len(pid_map)} closure objects. Roots: {injected_roots}")

    # Register in Main PrefabLib (PID MAIN_PREFABLIB_PID)
    if MAIN_PREFABLIB_PID in sf_b.objects:
        plib_obj = sf_b.objects[MAIN_PREFABLIB_PID]
        plib_tree = plib_obj.read_typetree()
        prefab_list = plib_tree.get("PrefabList", [])
        existing_pids = {p["Prefab"]["m_PathID"] for p in prefab_list if p.get("Prefab", {}).get("m_FileID") == 0}
        for rname, rpid in injected_roots.items():
            if rpid not in existing_pids:
                prefab_list.append({"Prefab": {"m_FileID": 0, "m_PathID": rpid}, "Amount": 3})
                print(f"  [+] Added {rname} (PID {rpid}) to main PrefabLib")
        plib_tree["PrefabList"] = prefab_list
        commit_obj_typetree(plib_obj, plib_tree)

    # Save blackout_cin_tf.assetbundle with LZ4
    print("[*] Saving patched blackout_cin_tf.assetbundle with packer='lz4'...")
    with open(BLACKOUT_BUNDLE_PATH, "wb") as f:
        f.write(env_b.file.save(packer="lz4"))
    print(f"[+] Successfully saved {BLACKOUT_BUNDLE_PATH} ({BLACKOUT_BUNDLE_PATH.stat().st_size} bytes)")


def patch_moves_bundle():
    print("\n[*] Loading moves.assetbundle...")
    env_m = UnityPy.load(str(MOVES_BUNDLE_PATH))
    sf_m = list(env_m.assets)[0]

    env_net = UnityPy.load(str(NETFLIX_MOVES_PATH))
    sf_net = list(env_net.assets)[0]

    scorp_s1_obj = sf_net.objects[SCORP_S1_MOVE_PID]
    scorp_s1_tree = copy.deepcopy(scorp_s1_obj.read_typetree())
    scorp_data = json.loads(scorp_s1_tree["m_Script"])

    new_data = {
        "moves": {
            "id": "move_blackout_special_01",
            "m_Name": "move_blackout_special_01",
            "meta": scorp_data.get("moves", {}).get("meta", {"f": [], "s": []}),
            "events": []
        }
    }

    # Filter & customize events from Scorponok S1
    for ev in scorp_data.get("moves", {}).get("events", []):
        ev["mn"] = "move_blackout_special_01"
        ev_type = ev.get("type") or ev.get("$type", "").split(".")[-1].split(",")[0]
        if ev_type == "PlayPropAnimatorStateMoveEvent":
            # Remove clawleft, clawright, tail prop events
            continue

        if ev_type == "ProjectileMoveEvent":
            pn = ev.get("pn", "")
            ev["pn"] = "projectile_jetfire_sp1_bullet"
            ev["dn"] = "projectile_jetfire_sp1_bullet"
            # Note: Keep of and oe empty so Projectile uses its native MoveToPlayOnFire ("fire") & MoveToPlayOnExplode ("explode")!
            ev["of"] = ""
            ev["oe"] = ""
            ev["spd"] = 120

            # First projectile (f=10) - Raised y from 5.5 to 8.0 to align with Blackout's extended arm/gun muzzle
            if ev.get("f", 0) <= 15:
                ev["f"] = 10
                ev["po"] = {"o": {"x": 0.0, "y": 8.0, "z": 5.8}, "s": 1}
                ev["hd"] = {
                    "al": 16,
                    "at": 2,
                    "idx": 0,
                    "dam": 0.5,
                    "db": False,
                    "fd": False,
                    "hr": "HitReactionMediumBackHigh",
                    "hs": 25,
                    "kb": 18,
                    "m": 0.5,
                    "u": False,
                    "bhs": 15,
                    "bkb": 8,
                    "bft": 0,
                    "ft": 0
                }
            # Second projectile (f=32) -> Unblockable last hit!
            else:
                ev["f"] = 32
                ev["po"] = {"o": {"x": 0.0, "y": 5.0, "z": 5.2}, "s": 1}
                ev["hd"] = {
                    "al": 16,
                    "at": 2,
                    "idx": 100,
                    "dam": 0.5,
                    "db": True,
                    "fd": False,
                    "hr": "HitReactionHeavyBack",
                    "hs": 25,
                    "kb": 22,
                    "m": 0.5,
                    "u": True,          # Unblockable!
                    "bhs": 12,
                    "bkb": 7,
                    "bft": 0,
                    "ft": 0
                }

        new_data["moves"]["events"].append(ev)

    # Serialize into TextAsset typetree
    scorp_s1_tree["m_Name"] = "move_blackout_special_01"
    scorp_s1_tree["m_Script"] = json.dumps(new_data)

    new_s1_obj = copy.copy(scorp_s1_obj)
    new_s1_obj.path_id = BLACKOUT_S1_MOVE_PID
    commit_obj_typetree(new_s1_obj, scorp_s1_tree)
    sf_m.objects[BLACKOUT_S1_MOVE_PID] = new_s1_obj
    print(f"[+] Replaced move_blackout_special_01 (PID {BLACKOUT_S1_MOVE_PID}) based on Scorponok S1 events + Jetfire projectiles!")

    # Verify AssetBundle m_Container
    for obj in sf_m.objects.values():
        if obj.type.name == "AssetBundle":
            ab_tree = obj.read_typetree()
            container = ab_tree.get("m_Container", [])
            has_s1 = any(c[0] == "assets/bundles/movedata/move_blackout_special_01.txt" for c in container)
            if not has_s1:
                container.append([
                    "assets/bundles/movedata/move_blackout_special_01.txt",
                    {"preloadIndex": 0, "preloadSize": 0, "asset": {"m_FileID": 0, "m_PathID": BLACKOUT_S1_MOVE_PID}}
                ])
                ab_tree["m_Container"] = container
                commit_obj_typetree(obj, ab_tree)
                print("[+] Added move_blackout_special_01.txt to moves.assetbundle container")

    # Save moves.assetbundle with LZ4
    print("[*] Saving patched moves.assetbundle with packer='lz4'...")
    with open(MOVES_BUNDLE_PATH, "wb") as f:
        f.write(env_m.file.save(packer="lz4"))
    print(f"[+] Successfully saved {MOVES_BUNDLE_PATH} ({MOVES_BUNDLE_PATH.stat().st_size} bytes)")


if __name__ == "__main__":
    patch_blackout_bundle()
    patch_moves_bundle()
    print("\n[ALL COMPLETE] Scorponok S1 animation & audio + Jetfire S1 projectile successfully grafted to Blackout!")
