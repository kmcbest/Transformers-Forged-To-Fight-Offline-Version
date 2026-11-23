import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

env = UnityPy.load(r"E:\Agent\TFTF\assets_redeco\blitzwing_gs.assetbundle")
CHAR_FIGHT_AOC_PID = -7755666207738536548
CHAR_FIGHT_AC_PID = -6923321525341018075

ac_obj = None
aoc_obj = None
for obj in env.objects:
    if obj.path_id == CHAR_FIGHT_AC_PID:
        ac_obj = obj.read_typetree()
    elif obj.path_id == CHAR_FIGHT_AOC_PID:
        aoc_obj = obj.read_typetree()

# Map states in AC to motion / clips
states_info = {}
for sm in ac_obj.get("m_Controller", {}).get("m_StateMachineArray", []):
    for st in sm.get("data", sm).get("m_StateConstantArray", []):
        d = st.get("data", st)
        nid = d.get("m_NameID")
        motion = d.get("m_Motion")
        states_info[nid] = motion

print(f"Total entries in AOC: {len(aoc_obj.get('m_Clips', []))}")
for idx, entry in enumerate(aoc_obj.get("m_Clips", [])):
    orig_pid = entry["m_OriginalClip"]["m_PathID"]
    ovr_pid = entry["m_OverrideClip"]["m_PathID"]
    print(f"[{idx:02d}] orig_pid={orig_pid:<22} -> ovr_pid={ovr_pid}")
