import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

bp = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\prowl_gs_deluxe2016_odr\prowl_gs_deluxe2016.assetbundle")
env = UnityPy.load(str(bp))

for obj in env.objects:
    if obj.type.name == "AnimatorOverrideController":
        tree = obj.read_typetree()
        print("Controller Name:", tree.get("m_Name"))
        print("Controller Ref:", tree.get("m_Controller"))
        clips = tree.get("m_Clips", [])
        print(f"Total clips: {len(clips)}")
        # Let's inspect the overrides
        for c in clips:
            orig = c.get("m_OriginalClip", {})
            over = c.get("m_OverrideClip", {})
            print(f"  Orig: {orig} -> Over: {over}")
