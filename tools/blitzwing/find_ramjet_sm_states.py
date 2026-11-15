import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

bundle_path = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\ramjet_gs_deluxe2008_odr\ramjet_gs_deluxe2008.assetbundle"
env = UnityPy.load(bundle_path)
obj_map = {o.path_id: o for o in env.objects}

ac = obj_map.get(-6923321525341018075) # animator_char_fight
tt = ac.read_typetree()

ctrl = tt.get("m_Controller", {})
states = []
def scan_sm(sm):
    for st in sm.get("m_States", []):
        s = st.get("m_State", {})
        states.append(s)
    for sub in sm.get("m_ChildStateMachines", []):
        scan_sm(sub.get("m_StateMachine", {}))

for sm in ctrl.get("m_StateMachineArray", []):
    scan_sm(sm)

print(f"Total states found: {len(states)}")
for s in states:
    name = s.get("m_Name", "")
    if "heavy" in name.lower() or "attack" in name.lower():
        print(f"State: {name}, Motion: {s.get('m_Motion')}")
