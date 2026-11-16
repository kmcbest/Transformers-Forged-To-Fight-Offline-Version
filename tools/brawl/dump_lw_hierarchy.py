import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

BASE_DIR = Path(r"E:\Agent\TFTF-blender")
BRAWL_BUNDLE = BASE_DIR / r"assets_redeco\brawl_gs.assetbundle"
env = UnityPy.load(str(BRAWL_BUNDLE))
obj_map = {o.path_id: o for o in env.objects}

def print_tree(trans_pid, depth=0):
    t_obj = obj_map.get(trans_pid)
    if not t_obj:
        print("  "*depth + f"MISSING Transform {trans_pid}")
        return
    t_tt = t_obj.read_typetree()
    go_pid = t_tt.get("m_GameObject", {}).get("m_PathID")
    go_obj = obj_map.get(go_pid)
    go_name = go_obj.read_typetree().get("m_Name") if go_obj else "MISSING_GO"
    
    # check components on GO
    comps = []
    if go_obj:
        for c in go_obj.read_typetree().get("m_Component", []):
            cpid = c['component']['m_PathID']
            co = obj_map.get(cpid)
            if co and co.type.name != "Transform":
                comps.append(f"{co.type.name}({cpid})")
    
    comp_str = f" [{', '.join(comps)}]" if comps else ""
    print("  "*depth + f"- {go_name} (GO={go_pid}, T={trans_pid}){comp_str}")
    
    for child in t_tt.get("m_Children", []):
        print_tree(child["m_PathID"], depth + 1)

root_trans_pid = -5632027485156562896
print("=== Hierarchy of Megatron_Cin_ROTF_lw ===")
print_tree(root_trans_pid)
