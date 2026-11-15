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
            print("  Root SM states:", len(sm.get("m_States", [])))
            for s in sm.get("m_States", []):
                st = s.get("m_State", {})
                print("   State:", st.get("m_Name"), "Motion:", st.get("m_Motion"))
            for sub in sm.get("m_ChildStateMachines", []):
                sub_sm = sub.get("m_StateMachine", {})
                print("   Sub SM:", sub_sm.get("m_Name"), "states:", len(sub_sm.get("m_States", [])))
                for s in sub_sm.get("m_States", []):
                    st = s.get("m_State", {})
                    if "attack" in st.get("m_Name", "").lower() or "heavy" in st.get("m_Name", "").lower():
                        print("     Sub State:", st.get("m_Name"), "Motion:", st.get("m_Motion"))
