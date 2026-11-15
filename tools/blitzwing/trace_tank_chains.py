import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = Path("e:/Agent/TFTF-blender/assets_redeco/blitzwing_gs.assetbundle")
env = UnityPy.load(str(bundle_path))
obj_map = {o.path_id: o for o in env.objects}

def print_chain(start_pid, title):
    print(f"\n--- {title} ---")
    cur = start_pid
    while cur != 0 and cur in obj_map:
        tr = obj_map[cur].read_typetree()
        go_pid = tr['m_GameObject']['m_PathID']
        go = obj_map[go_pid].read_typetree()
        print(f"  Tr {cur}: GO='{go['m_Name']}' Active={go['m_IsActive']} pos={tr.get('m_LocalPosition')} rot={tr.get('m_LocalRotation')} scale={tr.get('m_LocalScale')}")
        father = tr.get("m_Father")
        cur = father.get("m_PathID") if father else 0

# Showcase Tank SMR GO Transform: -4070916873066828308
# Showcase Tank COG: -7543220954911659241
print_chain(-4070916873066828308, "Showcase Tank SMR GO Chain")
print_chain(-7543220954911659241, "Showcase Tank COG Chain")

# Combat Tank SMR GO Transform: -3207237225000537856
# Combat Tank COG: -7942071043123098758
print_chain(-3207237225000537856, "Combat Tank SMR GO Chain")
print_chain(-7942071043123098758, "Combat Tank COG Chain")

# Combat Jet SMR GO Transform: -5727109540658706581
# Combat Jet COG: 4936350875999462921
print_chain(-5727109540658706581, "Combat Jet SMR GO Chain")
print_chain(4936350875999462921, "Combat Jet COG Chain")
