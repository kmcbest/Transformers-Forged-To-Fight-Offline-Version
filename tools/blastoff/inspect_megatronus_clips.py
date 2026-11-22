import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

ROOT = Path(r"E:\Agent\TFTF-blender")
DONOR = ROOT / "extracted_apk/assets/assetpack/megatronus_gs_kabam_odr/megatronus_gs_kabam.assetbundle"
env = UnityPy.load(str(DONOR))

clips = [o for o in env.objects if o.type.name == "AnimationClip"]
print(f"Total AnimationClips in Megatronus donor: {len(clips)}")
for c in clips[:3]:
    tt = c.read_typetree()
    name = tt.get("m_Name", "")
    print(f"\nAnimationClip: {name}")
    # Inspect animated paths / curves
    curves = tt.get("m_ClipBindingConstant", {}).get("genericBindings", [])
    path_types = {}
    for b in curves:
        attr = b.get("attribute")
        path = b.get("path")
        path_types[attr] = path_types.get(attr, 0) + 1
    print(f"  Generic bindings attribute counts: {path_types}")
