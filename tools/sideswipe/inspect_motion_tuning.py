import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
SS_BUNDLE = ROOT / "assets_redeco" / "sideswipe_cin_rotf.assetbundle"
DONOR_BARRICADE = ROOT / "extracted_apk" / "assets" / "assetpack" / "barricade_cin_dotm_odr" / "barricade_cin_dotm.assetbundle"

print("=== 1. Inspecting Barricade / Sideswipe AOCs ===")
env = UnityPy.load(str(SS_BUNDLE))
obj_map = {o.path_id: o for o in env.objects}

for o in env.objects:
    if o.type.name == "AnimatorOverrideController":
        tt = o.read_typetree()
        print(f"\nAOC {o.path_id}: {tt.get('m_Name')}")
        for i, cl in enumerate(tt.get("m_Clips", [])):
            orig = cl.get("m_OriginalClip", {})
            over = cl.get("m_OverrideClip", {})
            print(f"  Slot {i:02d}: orig={orig.get('m_PathID')} -> over={over.get('m_FileID')}:{over.get('m_PathID')}")

print("\n=== 2. Inspecting PlayerReferences in Sideswipe Prefabs ===")
for o in env.objects:
    if o.type.name == "MonoBehaviour":
        tt = o.read_typetree()
        if "SpecialStagePrefab" in tt or "VictoryStagePrefab" in tt:
            print(f"PlayerReferences PID={o.path_id}:")
            print(f"  SpecialStagePrefab: {tt.get('SpecialStagePrefab')}")
            print(f"  VictoryStagePrefab: {tt.get('VictoryStagePrefab')}")
            print(f"  StageCameraRigPrefab: {tt.get('StageCameraRigPrefab')}")

print("\n=== 3. Inspecting Matinee AOC / Override Controllers ===")
for o in env.objects:
    if o.type.name == "MonoBehaviour":
        tt = o.read_typetree()
        if "_overrideControllerList" in tt:
            print(f"MatineeAOC PID={o.path_id}:")
            for item in tt.get("_overrideControllerList", []):
                print(f"  StateHash={item.get('StateHash')}: {item.get('OverrideClipName')}")
