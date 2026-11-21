import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

ROOT = Path(r"E:\Agent\TFTF-blender")

def get_aoc_slots(bundle_path):
    env = UnityPy.load(str(bundle_path))
    sf = list(env.assets)[0]
    clip_names = {}
    for pid, o in sf.objects.items():
        if o.type.name == "AnimationClip":
            clip_names[pid] = o.read_typetree().get("m_Name")
    
    # Also load procedural
    proc_p = ROOT / "extracted_apk" / "assets" / "assetpack" / "characters_procedural_odr" / "character_anim_procedural.assetbundle"
    if proc_p.is_file():
        env_p = UnityPy.load(str(proc_p))
        sf_p = list(env_p.assets)[0]
        for pid, o in sf_p.objects.items():
            if o.type.name == "AnimationClip":
                clip_names[pid] = o.read_typetree().get("m_Name")

    for pid, o in sf.objects.items():
        if o.type.name == "AnimatorOverrideController":
            tt = o.read_typetree()
            if "fight" in tt.get("m_Name", "").lower():
                print(f"\n{bundle_path.stem} -> {tt.get('m_Name')}:")
                for idx, cl in enumerate(tt.get("m_Clips", [])):
                    orig_pid = cl.get("m_OriginalClip", {}).get("m_PathID")
                    over = cl.get("m_OverrideClip", {})
                    opid = over.get("m_PathID")
                    oname = clip_names.get(opid, f"PID:{opid}")
                    origname = clip_names.get(orig_pid, f"PID:{orig_pid}")
                    if "idle" in oname.lower() or "idle" in origname.lower() or idx in (0, 1, 2, 3):
                        print(f"  Slot {idx:02d} ({origname}): {oname} (over={over})")

get_aoc_slots(ROOT / "assets_redeco" / "sideswipe_cin_rotf.assetbundle")
get_aoc_slots(ROOT / "extracted_apk" / "assets" / "assetpack" / "necrotronus_gs_kabam_odr" / "necrotronus_gs_kabam.assetbundle")
get_aoc_slots(ROOT / "extracted_apk" / "assets" / "assetpack" / "megatronus_gs_kabam_odr" / "megatronus_gs_kabam.assetbundle")
