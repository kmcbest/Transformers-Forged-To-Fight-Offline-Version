import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

bundle_path = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\ramjet_gs_deluxe2008_odr\ramjet_gs_deluxe2008.assetbundle"
env = UnityPy.load(bundle_path)
obj_map = {o.path_id: o for o in env.objects}

ac = obj_map.get(-6923321525341018075)
tt = ac.read_typetree()
sm_data = tt["m_Controller"]["m_StateMachineArray"][0]["data"]
for i, st in enumerate(sm_data.get("m_StateConstantArray", [])):
    data = st.get("data", st)
    if data.get("m_NameID") == 2579208148: # HeavyAttack
        print(f"HeavyAttack StateConstant [{i}]:", data)
        # Find motion in m_Values
        # In Unity AnimatorController, m_Values or m_AnimationClips
        print("m_AnimationClips len:", len(tt.get("m_AnimationClips", [])))
