import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

env = UnityPy.load(r"E:\Agent\TFTF\assets_redeco\blitzwing_gs.assetbundle")
CHAR_FIGHT_AC_PID = -6923321525341018075
for obj in env.objects:
    if obj.path_id == CHAR_FIGHT_AC_PID:
        ac = obj.read_typetree()
        clips = ac.get("m_AnimationClips", [])
        controller = ac.get("m_Controller", {})
        # Look for m_ClipInfoArray or similar
        for sm in controller.get("m_StateMachineArray", []):
            states = sm.get("data", sm).get("m_StateConstantArray", [])
            for idx, st in enumerate(states):
                d = st.get("data", st)
                nid = d.get("m_NameID")
                # print any field that looks like an index
                print(f"State [{idx:02d}] NameID={nid}: {[(k, v) for k, v in d.items() if 'clip' in k.lower() or 'index' in k.lower() or 'motion' in k.lower() or 'blend' in k.lower()]}")
        break
