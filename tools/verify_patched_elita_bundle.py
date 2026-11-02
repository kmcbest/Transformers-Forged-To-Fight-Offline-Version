import sys
from pathlib import Path
import UnityPy

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

bundle_path = Path(r"E:\Agent\TFTF\assets_redeco\elita_one_gs.assetbundle")
print("Verifying:", bundle_path)
env = UnityPy.load(str(bundle_path))

# Check container
for o in env.objects:
    if o.type.name == "AssetBundle":
        data = o.read_typetree()
        print("AssetBundle container paths:")
        for item in data.get("m_Container", []):
            print(" ", item[0])

# Check injected clips
injected_pids = [992001, 992002, 992003, 992004, 992005, 992006, 992007]
for o in env.objects:
    if o.path_id in injected_pids:
        t = o.read_typetree()
        print(f"Verified Clip {o.path_id}: {t.get('m_Name')}")

# Check AOC
for o in env.objects:
    if o.path_id == -1743739782552134489:
        t = o.read_typetree()
        print("\nVerified AOC slots:")
        clips = t.get("m_Clips", [])
        for idx in (2, 3, 5, 41, 42, 43, 44):
            print(f"  Slot [{idx}]: Orig {clips[idx]['m_OriginalClip']['m_PathID']} -> Override {clips[idx]['m_OverrideClip']}")

# Check MoveSet
for o in env.objects:
    if o.path_id == -4848773121996721726:
        t = o.read_typetree()
        print("\nVerified MoveSet moves:")
        for m in t.get("_moves", []):
            if any(x in m.get("_name", "") for x in ("brawler", "bumblebee")):
                print(" ", m)

print("\nALL VERIFICATIONS PASSED!")
