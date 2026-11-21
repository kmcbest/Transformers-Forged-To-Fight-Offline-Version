import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

ROOT = Path(r"E:\Agent\TFTF-blender")

def check_clip_type(bundle_path, clip_pid):
    env = UnityPy.load(str(bundle_path))
    sf = list(env.assets)[0]
    clip = sf.objects[clip_pid].read_typetree()
    cname = clip.get("m_Name")
    print(f"\nClip {cname}:")
    print(f"  m_AnimationType: {clip.get('m_AnimationType')}")
    print(f"  m_Legacy: {clip.get('m_Legacy')}")
    bindings = clip.get("m_ClipBindingConstant", {}).get("genericBindings", [])
    type_ids = {b.get("typeID") for b in bindings}
    print(f"  typeIDs in bindings: {type_ids}")
    # Print sample bindings
    for b in bindings[:5]:
        print(f"    path={b.get('path')}, attr={b.get('attribute')}, typeID={b.get('typeID')}")

check_clip_type(ROOT / "assets_redeco" / "sideswipe_cin_rotf.assetbundle", -2652520226880806548)
check_clip_type(ROOT / "extracted_apk" / "assets" / "assetpack" / "necrotronus_gs_kabam_odr" / "necrotronus_gs_kabam.assetbundle", -8455018533602519118)
check_clip_type(ROOT / "extracted_apk" / "assets" / "assetpack" / "megatronus_gs_kabam_odr" / "megatronus_gs_kabam.assetbundle", -341588482639063847)
