import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

BASE_DIR = Path(r"E:\Agent\TFTF-blender")
BRAWL_BUNDLE = BASE_DIR / r"assets_redeco\brawl_gs.assetbundle"
DONOR_BUNDLE = BASE_DIR / r"extracted_apk\assets\assetpack\megatron_cin_rotf_odr\megatron_cin_rotf.assetbundle"

for bpath, label in [(DONOR_BUNDLE, "Donor"), (BRAWL_BUNDLE, "Brawl")]:
    env = UnityPy.load(str(bpath))
    obj_map = {o.path_id: o for o in env.objects}
    
    lw_go_pid = 7253228804562187563
    go = obj_map[lw_go_pid].read_typetree()
    print(f"[{label}] Root LW GO: {go.get('m_Name')}")
    print(f"  Components: {len(go.get('m_Component', []))}")
    for c in go.get('m_Component', []):
        c_pid = c['component']['m_PathID']
        c_obj = obj_map.get(c_pid)
        print(f"    Component PID={c_pid} Type={c_obj.type.name if c_obj else 'MISSING'}")
        if c_obj and c_obj.type.name == "Animator":
            att = c_obj.read_typetree()
            print(f"      Animator Controller: {att.get('m_Controller')}")
        elif c_obj and c_obj.type.name == "MonoBehaviour":
            mtt = c_obj.read_typetree()
            script_pid = mtt.get("m_Script", {}).get("m_PathID")
            script_fid = mtt.get("m_Script", {}).get("m_FileID")
            print(f"      MonoBehaviour script: FileID={script_fid}, PathID={script_pid}")
