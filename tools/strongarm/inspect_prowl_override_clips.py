import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\prowl_gs_deluxe2016_odr\prowl_gs_deluxe2016.assetbundle")
env = UnityPy.load(str(bundle_path))

for obj in env.objects:
    if obj.type.name == "AnimatorOverrideController":
        tree = obj.read_typetree()
        print(f"\nOverrideController: {tree.get('m_Name')}")
        clips = tree.get("m_Clips", [])
        print(f"Total clips: {len(clips)}")
        for c in clips:
            orig = c.get("m_OriginalClip", {})
            over = c.get("m_OverrideClip", {})
            print(f"  Orig: fileID={orig.get('m_FileID')}, pathID={orig.get('m_PathID')} -> Over: fileID={over.get('m_FileID')}, pathID={over.get('m_PathID')}")
