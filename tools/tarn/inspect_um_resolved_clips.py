import sys
import json
import UnityPy

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

UM_PATH = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\ultramagnus_gs_leader_odr\ultramagnus_gs_leader.assetbundle"
PROC_PATH = r"E:\Agent\TFTF-blender\assets_netflix\character_anim_procedural.assetbundle"
MOVES_PATH = r"E:\Agent\TFTF-blender\assets_netflix\moves.assetbundle"


def main():
    env = UnityPy.load(UM_PATH)
    penv = UnityPy.load(PROC_PATH)
    menv = UnityPy.load(MOVES_PATH)

    clip_names = {}
    for src in (env, penv):
        for o in src.objects:
            if o.type.name == "AnimationClip":
                clip_names[o.path_id] = o.read_typetree().get("m_Name", f"<{o.path_id}>")

    print("=== Resolved Ultra Magnus AnimatorOverrideControllers ===")
    for o in env.objects:
        if o.type.name == "AnimatorOverrideController":
            tt = o.read_typetree()
            print(f"\nAOC '{tt.get('m_Name')}' (PID={o.path_id}):")
            for pair in tt.get("m_Clips", []):
                opid = pair["m_OriginalClip"]["m_PathID"]
                rpid = pair["m_OverrideClip"]["m_PathID"]
                print(f"  [{opid:21d}] {clip_names.get(opid, '<unknown>'):44s} -> {clip_names.get(rpid, '<unknown>')} ({rpid})")

    print("\n=== PropsController on UltraMagnus_GS_Leader (Showcase) ===")
    script_map = {o.path_id: o.read_typetree().get("m_Name", "?") for o in env.objects if o.type.name == "MonoScript"}
    go_map = {o.path_id: o.read_typetree().get("m_Name", "?") for o in env.objects if o.type.name == "GameObject"}
    for o in env.objects:
        if o.type.name == "MonoBehaviour":
            tt = o.read_typetree()
            sc = script_map.get(tt.get("m_Script", {}).get("m_PathID", 0), "")
            go = go_map.get(tt.get("m_GameObject", {}).get("m_PathID", 0), "")
            if go == "UltraMagnus_GS_Leader" and sc in ("PropsController", "MoveSet", "CharacterAudio"):
                print(f"\n  Script {sc}:")
                if sc == "PropsController":
                    keys = tt["_props"]["_serializedKeys"]
                    vals = tt["_props"]["_serializedValues"]
                    for k, v in zip(keys, vals):
                        print(f"    prop '{k}': PropType={v.get('PropType')} InitFlags={v.get('InitFlags')} RootPath='{v.get('RootPath')}' GUID={v.get('PrefabAssetGUID')} AOC={v.get('OverrideController',{}).get('m_PathID')}")
                elif sc == "MoveSet":
                    print(f"    _moves PIDs: {tt.get('_moves', [])}")

    print("\n=== Ultra Magnus moves in moves.assetbundle ===")
    for o in menv.objects:
        if o.type.name == "MonoBehaviour":
            tt = o.read_typetree()
            name = tt.get("m_Name", "")
            nl = name.lower()
            if "magnus" in nl or "tact" in nl:
                print(f"  PID={o.path_id:21d} '{name}' anim={tt.get('AnimationName','')} props={tt.get('PropSettings','') or tt.get('Props','')}")


if __name__ == "__main__":
    main()
