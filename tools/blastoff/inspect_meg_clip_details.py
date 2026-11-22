import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

BUNDLE_PATH = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatronus_gs_kabam_odr\megatronus_gs_kabam.assetbundle")
env = UnityPy.load(str(BUNDLE_PATH))

for obj in env.objects:
    if obj.type.name == "AnimationClip":
        tt = obj.read_typetree()
        cname = tt["m_Name"]
        paths = []
        for b in tt.get("m_ClipBindingConstant", {}).get("genericBindings", []):
            paths.append(str(b.get("path", "")))
        # Check if transformed or 01 is referenced
        print(f"Clip: {cname} | bindings={len(paths)} | sampleRate={tt.get('m_SampleRate')} | length={tt.get('m_MuscleClip', {}).get('m_StopTime', 0.0):.2f}s")
