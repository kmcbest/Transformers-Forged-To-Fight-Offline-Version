import sys
import json
import UnityPy

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

UM_PATH = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\ultramagnus_gs_leader_odr\ultramagnus_gs_leader.assetbundle"
PROC_PATH = r"E:\Agent\TFTF-blender\assets_netflix\character_anim_procedural.assetbundle"


def main():
    env = UnityPy.load(UM_PATH)
    objs = {o.path_id: o for o in env.objects}

    def nm(pid):
        o = objs.get(pid)
        if not o:
            return f"<{pid}>"
        try:
            return o.read_typetree().get("m_Name", f"<{o.type.name}:{pid}>")
        except Exception:
            return f"<{o.type.name}:{pid}>"

    print("=== AnimatorOverrideControllers in ultramagnus_gs_leader.assetbundle ===")
    for o in env.objects:
        if o.type.name == "AnimatorOverrideController":
            tt = o.read_typetree()
            print(f"\nAOC PID={o.path_id} '{tt.get('m_Name')}' baseController={nm(tt.get('m_Controller',{}).get('m_PathID',0))}")
            for pair in tt.get("m_Clips", []):
                orig = nm(pair["m_OriginalClip"]["m_PathID"])
                ovr = nm(pair["m_OverrideClip"]["m_PathID"])
                print(f"  {orig:42s} -> {ovr} (PID={pair['m_OverrideClip']['m_PathID']})")

    print("\n=== MonoBehaviours referencingProps / Attack / Weapon in Character Prefabs ===")
    go_map = {o.path_id: o.read_typetree().get("m_Name", "?") for o in env.objects if o.type.name == "GameObject"}
    script_map = {o.path_id: o.read_typetree().get("m_Name", "?") for o in env.objects if o.type.name == "MonoScript"}
    for o in env.objects:
        if o.type.name == "MonoBehaviour":
            tt = o.read_typetree()
            sc_pid = tt.get("m_Script", {}).get("m_PathID", 0)
            sc_name = script_map.get(sc_pid, str(sc_pid))
            go_pid = tt.get("m_GameObject", {}).get("m_PathID", 0)
            go_name = go_map.get(go_pid, "?")
            if go_name in ("UltraMagnus_GS_Leader", "UltraMagnus_GS_Leader_lw", "character_model") or "Prop" in sc_name or "Special" in sc_name or "Character" in sc_name:
                keys = [k for k in tt.keys() if not k.startswith("m_")]
                print(f"  MB PID={o.path_id} GO='{go_name}' script='{sc_name}' keys={keys[:15]}")
                if "_props" in str(tt).lower() or "prop" in sc_name.lower() or "special" in sc_name.lower():
                    print(f"    data={json.dumps(tt, default=str)[:500]}")

    print("\n=== Tactical & UltraMagnus AnimationClips in character_anim_procedural.assetbundle ===")
    penv = UnityPy.load(PROC_PATH)
    tact_clips = []
    for o in penv.objects:
        if o.type.name == "AnimationClip":
            tt = o.read_typetree()
            name = tt.get("m_Name", "")
            nl = name.lower()
            if "ultramagnus" in nl or nl.startswith("tactical_") or "tactical" in nl or "truck" in nl:
                tact_clips.append((o.path_id, name))
    for pid, name in sorted(tact_clips, key=lambda x: x[1]):
        print(f"  Clip PID={pid:20d} '{name}'")


if __name__ == "__main__":
    main()
