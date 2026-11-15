import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

bundle_path = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\ramjet_gs_deluxe2008_odr\ramjet_gs_deluxe2008.assetbundle"
env = UnityPy.load(bundle_path)

for obj in env.objects:
    if obj.path_id == -6923321525341018075:
        tt = obj.read_typetree()
        print("Clips in animator_char_fight:")
        for ptr in tt.get("m_AnimationClips", []):
            print(f"  FileID={ptr.get('m_FileID')} PathID={ptr.get('m_PathID')}")
