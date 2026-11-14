import sys
import json
import UnityPy

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

UM_PATH = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\ultramagnus_gs_leader_odr\ultramagnus_gs_leader.assetbundle"
MOVES_PATH = r"E:\Agent\TFTF-blender\assets_netflix\moves.assetbundle"


def main():
    uenv = UnityPy.load(UM_PATH)
    menv = UnityPy.load(MOVES_PATH)
    mobjs = {o.path_id: o for o in menv.objects}
    uobjs = {o.path_id: o for o in uenv.objects}

    # Find Showcase MoveSet
    go_map = {o.path_id: o.read_typetree().get("m_Name", "?") for o in uenv.objects if o.type.name == "GameObject"}
    script_map = {o.path_id: o.read_typetree().get("m_Name", "?") for o in uenv.objects if o.type.name == "MonoScript"}

    for o in uenv.objects:
        if o.type.name == "MonoBehaviour":
            tt = o.read_typetree()
            sc = script_map.get(tt.get("m_Script", {}).get("m_PathID", 0), "")
            go = go_map.get(tt.get("m_GameObject", {}).get("m_PathID", 0), "")
            if go == "UltraMagnus_GS_Leader" and sc == "MoveSet":
                print("=== UltraMagnus Showcase MoveSet ===")
                for entry in tt.get("_moves", []):
                    mname = entry.get("_name", "")
                    state = entry.get("_animStateName", "")
                    ap = entry.get("_asset", {})
                    pid = ap.get("m_PathID", 0)
                    fid = ap.get("m_FileID", 0)
                    mobj = mobjs.get(pid) or uobjs.get(pid)
                    extra = ""
                    if mobj:
                        try:
                            mtt = mobj.read_typetree()
                            # check props / projectiles / submoves / duration
                            interesting = {}
                            for k in ("_animation", "_duration", "_propActions", "_props", "_projectiles", "_rangedActions", "_events", "_subMoves"):
                                if k in mtt and mtt[k]:
                                    interesting[k] = mtt[k]
                            extra = json.dumps(interesting, default=str)[:320]
                        except Exception as e:
                            extra = f"<err {e}>"
                    print(f"  {state:34s} | {mname:42s} | fid={fid} pid={pid:21d} | {extra}")

    print("\n=== UltraMagnus Heavy / SP1 / SP2 / SP3 clip lengths & animated paths ===")
    for o in uenv.objects:
        if o.type.name == "AnimationClip":
            name = o.read().m_Name
            if any(k in name.lower() for k in ("special", "heavy", "combatidle")):
                tt = o.read_typetree()
                # Check curve bindings to see which bones/GPs move!
                bindings = []
                gcb = tt.get("m_ClipBindingConstant", {}).get("genericBindings", [])
                for b in gcb[:15]:
                    bindings.append(b.get("path", 0))
                print(f"  Clip '{name}': len={tt.get('m_Muscles', []) and tt.get('m_Clip',{}).get('m_StopTime') or tt.get('m_SampleRate')} gcb_count={len(gcb)}")


if __name__ == "__main__":
    main()
