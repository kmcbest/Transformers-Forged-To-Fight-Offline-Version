import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

bundle_path = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\ramjet_gs_deluxe2008_odr\ramjet_gs_deluxe2008.assetbundle"
env = UnityPy.load(bundle_path)

obj_map = {o.path_id: o for o in env.objects}
ctrl = obj_map.get(-6340484879223379266)
if ctrl:
    tt = ctrl.read_typetree()
    print("AnimatorController Name:", tt.get("m_Name"))
    for clip in tt.get("m_AnimationClips", []):
        print(f"  Clip FileID={clip.get('m_FileID')} PathID={clip.get('m_PathID')}")
        if clip.get('m_FileID') == 0:
            cobj = obj_map.get(clip.get('m_PathID'))
            if cobj:
                print("    Internal Clip Name:", cobj.read_typetree().get("m_Name"))
