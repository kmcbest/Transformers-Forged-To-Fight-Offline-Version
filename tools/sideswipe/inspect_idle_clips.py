import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

ROOT = Path(r"E:\Agent\TFTF-blender")

def inspect_aoc_idles(bundle_path, bot_name):
    env = UnityPy.load(str(bundle_path))
    sf = list(env.assets)[0]
    print(f"\n==================== {bot_name} ====================")
    for pid, o in sf.objects.items():
        if o.type.name == "AnimatorOverrideController":
            tt = o.read_typetree()
            name = tt.get("m_Name", "")
            if "fight" in name.lower() or "lw" in name.lower():
                print(f"AOC PID={pid}, Name={name}")
                for idx, cl in enumerate(tt.get("m_Clips", [])):
                    orig_pid = cl.get("m_OriginalClip", {}).get("m_PathID")
                    over = cl.get("m_OverrideClip", {})
                    # Let's inspect first 15 slots (usually idles, transitions)
                    if idx < 15 or any(k in str(over) for k in ["idle", "Idle", "feral", "combat"]):
                        print(f"  Slot {idx:02d} (orig {orig_pid}): over={over.get('m_FileID')}:{over.get('m_PathID')}")

    # Also list all AnimationClips in bundle
    clips = []
    for pid, o in sf.objects.items():
        if o.type.name == "AnimationClip":
            tt = o.read_typetree()
            cname = tt.get("m_Name", "")
            if "idle" in cname.lower() or "stand" in cname.lower() or "pose" in cname.lower():
                clips.append((pid, cname))
    print(f"Local idle/stand clips in {bot_name}:")
    for pid, cn in clips:
        print(f"  {pid}: {cn}")

inspect_aoc_idles(ROOT / "assets_redeco" / "sideswipe_cin_rotf.assetbundle", "Sideswipe")
inspect_aoc_idles(ROOT / "extracted_apk" / "assets" / "assetpack" / "necrotronus_gs_kabam_odr" / "necrotronus_gs_kabam.assetbundle", "Necrotronus")
inspect_aoc_idles(ROOT / "extracted_apk" / "assets" / "assetpack" / "megatronus_gs_kabam_odr" / "megatronus_gs_kabam.assetbundle", "Megatronus")
