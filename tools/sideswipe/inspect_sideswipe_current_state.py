import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
bundle_path = ROOT / "assets_redeco" / "sideswipe_cin_rotf.assetbundle"

env = UnityPy.load(str(bundle_path))
sf = list(env.assets)[0]

print(f"=== Inspecting {bundle_path.name} ===")
print(f"Total objects: {len(sf.objects)}")
print(f"Externals ({len(sf.externals)}):")
for idx, ext in enumerate(sf.externals, start=1):
    print(f"  [{idx}] {ext.path}")

# 1. AnimationClips
clips = []
for pid, o in sf.objects.items():
    if o.type.name == "AnimationClip":
        tt = o.read_typetree()
        clips.append((pid, tt.get("m_Name")))
print(f"\nLocal AnimationClips ({len(clips)}):")
for pid, name in clips:
    print(f"  {pid}: {name}")

# 2. PlayerReferences
for pid, o in sf.objects.items():
    if o.type.name == "MonoBehaviour":
        tt = o.read_typetree()
        if "SpecialStagePrefab" in tt or "VictoryStagePrefab" in tt:
            print(f"\nPlayerReferences PID={pid}:")
            print(f"  SpecialStagePrefab: {tt.get('SpecialStagePrefab')}")
            print(f"  VictoryStagePrefab: {tt.get('VictoryStagePrefab')}")

# 3. Fight AOC
for pid, o in sf.objects.items():
    if o.type.name == "AnimatorOverrideController":
        tt = o.read_typetree()
        print(f"\nAOC PID={pid}: {tt.get('m_Name')}")
        if "fight" in tt.get("m_Name", "").lower():
            for i, cl in enumerate(tt.get("m_Clips", [])):
                orig_pid = cl.get("m_OriginalClip", {}).get("m_PathID")
                over = cl.get("m_OverrideClip", {})
                if i in (4, 5, 31, 32, 39, 40, 44, 58):
                    print(f"  Slot {i:02d} (orig {orig_pid}): over={over.get('m_FileID')}:{over.get('m_PathID')}")

# 4. MatineeAOC
for pid, o in sf.objects.items():
    if o.type.name == "MonoBehaviour":
        tt = o.read_typetree()
        if "_overrideControllerList" in tt:
            print(f"\nMatineeAOC PID={pid}: count={len(tt.get('_overrideControllerList', []))}")
            for item in tt.get("_overrideControllerList", []):
                sh = item.get("StateHash")
                if sh in (297974710, 1671240305, -90944565, 944691146, -1919714467, 966217297, -204748204, -1459930005):
                    print(f"  StateHash={sh}: {item.get('OverrideClipName')}")

# 5. MoveSets
for pid, o in sf.objects.items():
    if o.type.name == "MonoBehaviour":
        tt = o.read_typetree()
        if "_moves" in tt:
            moves = tt.get("_moves", [])
            print(f"\nMoveSet PID={pid}: count={len(moves)}")
            for i in (4, 5, 6, 7, 43, 44):
                if i < len(moves):
                    print(f"  [{i:02d}] {moves[i].get('_name')}: {moves[i].get('_asset')}")
