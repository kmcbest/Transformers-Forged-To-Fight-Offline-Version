import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
SS_BUNDLE = ROOT / "assets_redeco" / "sideswipe_cin_rotf.assetbundle"
MOVES_BUNDLE = ROOT / "extracted_apk" / "assets" / "assetpack" / "characters" / "moves.assetbundle"

print("Loading moves bundle to resolve clip names...")
env_moves = UnityPy.load(str(MOVES_BUNDLE))
moves_names = {}
for o in env_moves.objects:
    if o.type.name == "AnimationClip":
        tt = o.read_typetree()
        moves_names[o.path_id] = tt.get("m_Name")

env_ss = UnityPy.load(str(SS_BUNDLE))
sf = list(env_ss.assets)[0]
externals = {i+1: ext.path for i, ext in enumerate(sf.externals)}
print(f"Sideswipe Externals: {externals}")

local_clips = {}
for o in env_ss.objects:
    if o.type.name == "AnimationClip":
        tt = o.read_typetree()
        local_clips[o.path_id] = tt.get("m_Name")

aoc = [o for o in env_ss.objects if o.path_id == -2047393535863576714][0]
tt = aoc.read_typetree()
print(f"\nAOC: {tt.get('m_Name')}")
for i, cl in enumerate(tt.get("m_Clips", [])):
    orig_pid = cl.get("m_OriginalClip", {}).get("m_PathID")
    over_fid = cl.get("m_OverrideClip", {}).get("m_FileID")
    over_pid = cl.get("m_OverrideClip", {}).get("m_PathID")
    
    orig_name = moves_names.get(orig_pid, f"orig_{orig_pid}")
    if over_fid == 0:
        over_name = local_clips.get(over_pid, f"local_{over_pid}")
    else:
        over_name = moves_names.get(over_pid, f"ext_fid{over_fid}_{over_pid}")
    print(f"Slot {i:02d}: {orig_name} -> {over_name} (fid={over_fid}, pid={over_pid})")
