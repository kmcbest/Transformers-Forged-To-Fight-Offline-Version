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
ANIM_PROC = ROOT / "extracted_apk" / "assets" / "assetpack" / "characters_procedural_odr" / "character_anim_procedural.assetbundle"

clip_names = {}
for bpath in [MOVES_BUNDLE, ANIM_PROC]:
    if bpath.exists():
        env_b = UnityPy.load(str(bpath))
        for o in env_b.objects:
            if o.type.name == "AnimationClip":
                tt = o.read_typetree()
                clip_names[o.path_id] = tt.get("m_Name")

env_ss = UnityPy.load(str(SS_BUNDLE))
local_clips = {o.path_id: o.read_typetree().get("m_Name") for o in env_ss.objects if o.type.name == "AnimationClip"}

aoc = [o for o in env_ss.objects if o.path_id == -2047393535863576714][0]
tt = aoc.read_typetree()
print(f"=== AOC: {tt.get('m_Name')} ===")
for i, cl in enumerate(tt.get("m_Clips", [])):
    orig_pid = cl.get("m_OriginalClip", {}).get("m_PathID")
    over_fid = cl.get("m_OverrideClip", {}).get("m_FileID")
    over_pid = cl.get("m_OverrideClip", {}).get("m_PathID")
    
    orig_name = clip_names.get(orig_pid, str(orig_pid))
    if over_fid == 0:
        over_name = local_clips.get(over_pid, str(over_pid))
    else:
        over_name = clip_names.get(over_pid, f"fid{over_fid}_{over_pid}")
    print(f"Slot {i:02d}: {orig_name:<45} -> {over_name}")
