import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
import zlib

env = UnityPy.load(r"E:\Agent\TFTF\assets_redeco\blitzwing_gs.assetbundle")
CHAR_FIGHT_AC_PID = -6923321525341018075
CHAR_FIGHT_AOC_PID = -7755666207738536548

ac = None
for obj in env.objects:
    if obj.path_id == CHAR_FIGHT_AC_PID:
        ac = obj.read_typetree()
        break

# In Unity AnimatorController, states have m_Motion index or clip index
# Let's inspect the controller structure
controller = ac.get("m_Controller", {})
clips = ac.get("m_AnimationClips", [])
print(f"AC AnimationClips: {len(clips)}")
for idx, c in enumerate(clips):
    print(f"  Clip [{idx}]: {c}")

sm_array = controller.get("m_StateMachineArray", [])
for sm_idx, sm in enumerate(sm_array):
    states = sm.get("data", sm).get("m_StateConstantArray", [])
    for st_idx, st in enumerate(states):
        d = st.get("data", st)
        nid = d.get("m_NameID")
        # Check motion
        m = d.get("m_Motion")
        blend = d.get("m_BlendTreeConstant")
        # Let's find out how motion maps to clip
        if nid in [1809527195, 4073873441, 2245349559, 2579208148, 732291567, 2997661781, 3316351171, 1540298080]:
            print(f"State NameID={nid}: motion={m}, leaf_info={d.get('m_LeafInfoArray')}")
