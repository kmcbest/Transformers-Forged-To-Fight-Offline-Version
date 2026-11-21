import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
DONORS_DIR = ROOT / "extracted_apk" / "assets" / "assetpack"

def inspect_bot_bundle(bid):
    p = DONORS_DIR / f"{bid}_odr" / f"{bid}.assetbundle"
    assert p.is_file(), f"Missing {p}"
    env = UnityPy.load(str(p))
    print(f"\n==================== {bid} ====================")
    
    # 1. PlayerReferences
    pref = None
    for o in env.objects:
        if o.type.name == "MonoBehaviour":
            tt = o.read_typetree()
            if "SpecialStagePrefab" in tt or "VictoryStagePrefab" in tt:
                pref = tt
                print(f"PlayerReferences PID={o.path_id}:")
                print(f"  SpecialStagePrefab: {tt.get('SpecialStagePrefab')}")
                print(f"  VictoryStagePrefab: {tt.get('VictoryStagePrefab')}")
                break

    # 2. Local AnimationClips
    clips = []
    for o in env.objects:
        if o.type.name == "AnimationClip":
            tt = o.read_typetree()
            clips.append((o.path_id, tt.get("m_Name")))
    print(f"Local AnimationClips ({len(clips)}):")
    for pid, cname in clips:
        print(f"  {pid}: {cname}")

    # 3. Fight AOC
    for o in env.objects:
        if o.type.name == "AnimatorOverrideController":
            tt = o.read_typetree()
            if "fight" in tt.get("m_Name", "").lower():
                print(f"\nFight AOC PID={o.path_id}: {tt.get('m_Name')}")
                for i, cl in enumerate(tt.get("m_Clips", [])):
                    orig_pid = cl.get("m_OriginalClip", {}).get("m_PathID")
                    over = cl.get("m_OverrideClip", {})
                    # Print interesting slots: M2, S1, S2, S3, Heavy, Victory
                    if i in (4, 5, 31, 32, 39, 40, 44, 58):
                        print(f"  Slot {i:02d} (orig {orig_pid}): over={over.get('m_FileID')}:{over.get('m_PathID')}")

    # 4. MatineeAOC
    for o in env.objects:
        if o.type.name == "MonoBehaviour":
            tt = o.read_typetree()
            if "_overrideControllerList" in tt:
                print(f"\nMatineeAOC PID={o.path_id}:")
                for item in tt.get("_overrideControllerList", []):
                    sh = item.get("StateHash")
                    if sh in (297974710, 1671240305, -90944565, 944691146, -1919714467, 966217297, -204748204, -1459930005):
                        print(f"  StateHash={sh}: {item.get('OverrideClipName')}")

inspect_bot_bundle("cheetor_bw_transmetal")
inspect_bot_bundle("drift_cin_aoe")
inspect_bot_bundle("sideswipe_gs")
inspect_bot_bundle("optimusprime_cin_tf")
