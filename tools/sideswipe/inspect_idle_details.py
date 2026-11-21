import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

ROOT = Path(r"E:\Agent\TFTF-blender")

def inspect_clip_curves(bundle_p, clip_pid):
    env = UnityPy.load(str(bundle_p))
    sf = list(env.assets)[0]
    clip_obj = sf.objects.get(clip_pid)
    if not clip_obj:
        print(f"Clip {clip_pid} not found in {bundle_p.name}")
        return
    tt = clip_obj.read_typetree()
    cname = tt.get("m_Name")
    print(f"\nClip {cname} (PID {clip_pid}) in {bundle_p.name}:")
    print(f"  Length: {tt.get('m_MuscleClip', {}).get('m_StopTime', 0):.2f}s")
    # Check sample curves or bindings
    clip_binding = tt.get("m_ClipBindingConstant", {})
    bindings = clip_binding.get("genericBindings", [])
    print(f"  Generic bindings count: {len(bindings)}")

inspect_clip_curves(ROOT / "assets_redeco" / "sideswipe_cin_rotf.assetbundle", -2652520226880806548) # feral_normal_idle_02
inspect_clip_curves(ROOT / "extracted_apk" / "assets" / "assetpack" / "necrotronus_gs_kabam_odr" / "necrotronus_gs_kabam.assetbundle", -8455018533602519118) # Prefight_Brawler_idle_Megatron
inspect_clip_curves(ROOT / "extracted_apk" / "assets" / "assetpack" / "megatronus_gs_kabam_odr" / "megatronus_gs_kabam.assetbundle", -341588482639063847) # Brute02_normal_CombatIdle
