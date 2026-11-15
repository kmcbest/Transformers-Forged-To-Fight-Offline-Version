import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

bundle_path = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\ramjet_gs_deluxe2008_odr\ramjet_gs_deluxe2008.assetbundle"
env = UnityPy.load(bundle_path)

for obj in env.objects:
    if obj.path_id in (-6923321525341018075, 6875678843721788313):
        tt = obj.read_typetree()
        print(f"\nAnimatorController {obj.path_id}: {tt.get('m_Name')}")
        for layer in tt.get("m_AnimationLayers", []):
            sm = layer.get("m_StateMachine", {})
            for state in sm.get("m_States", []):
                s = state.get("m_State", {})
                sname = s.get("m_Name", "")
                if "heavy" in sname.lower():
                    print(f"  State: {sname}, Motion: {s.get('m_Motion')}")
