import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

ROOT = Path(r"E:\Agent\TFTF-blender")

def inspect_clip_name_and_events(bundle_path, pid):
    env = UnityPy.load(str(bundle_path))
    sf = list(env.assets)[0]
    tt = sf.objects[pid].read_typetree()
    print(f"Clip {tt.get('m_Name')} (PID {pid}):")
    mclip = tt.get("m_MuscleClip", {})
    print(f"  StopTime: {mclip.get('m_StopTime')}")
    print(f"  StartTime: {mclip.get('m_StartTime')}")
    print(f"  LoopTime: {mclip.get('m_LoopTime')}")
    print(f"  ClipBindingConstant bindings: {len(tt.get('m_ClipBindingConstant', {}).get('genericBindings', []))}")

inspect_clip_name_and_events(ROOT / "extracted_apk" / "assets" / "assetpack" / "necrotronus_gs_kabam_odr" / "necrotronus_gs_kabam.assetbundle", -8455018533602519118)
inspect_clip_name_and_events(ROOT / "extracted_apk" / "assets" / "assetpack" / "megatronus_gs_kabam_odr" / "megatronus_gs_kabam.assetbundle", -341588482639063847)
