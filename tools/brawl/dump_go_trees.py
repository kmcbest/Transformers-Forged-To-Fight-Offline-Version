import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
MEG_BUNDLE = ROOT / "extracted_apk" / "assets" / "assetpack" / "megatron_cin_rotf_odr" / "megatron_cin_rotf.assetbundle"
BRAWL_BUNDLE = ROOT / "assets_redeco" / "brawl_gs.assetbundle"

def dump_tree(bundle_path, root_name):
    env = UnityPy.load(str(bundle_path))
    sf = list(env.assets)[0]
    
    # find root
    root_go = None
    for pid, obj in sf.objects.items():
        if obj.type.name == "GameObject":
            tt = obj.read_typetree()
            if tt["m_Name"] == root_name:
                root_go = (pid, obj, tt)
                break
    if not root_go:
        print(f"Could not find {root_name} in {bundle_path.name}")
        return
        
    print(f"\n=== Dump Tree: {root_name} in {bundle_path.name} ===")
    
    # find transform
    def get_tr(go_tt):
        for comp in go_tt.get("m_Component", []):
            c_pid = comp["component"]["m_PathID"]
            c_obj = sf.objects.get(c_pid)
            if c_obj and c_obj.type.name in ("Transform", "RectTransform"):
                return c_obj.read_typetree()
        return None
        
    def walk(go_pid, depth=0):
        go_obj = sf.objects.get(go_pid)
        if not go_obj:
            return
        go_tt = go_obj.read_typetree()
        name = go_tt.get("m_Name", "")
        comps = []
        for comp in go_tt.get("m_Component", []):
            c_pid = comp["component"]["m_PathID"]
            c_obj = sf.objects.get(c_pid)
            comps.append(c_obj.type.name if c_obj else "NULL")
        print("  " * depth + f"- {name} (PID={go_pid}, comps={comps})")
        tr = get_tr(go_tt)
        if tr:
            for child in tr.get("m_Children", []):
                ch_tr_pid = child["m_PathID"]
                ch_tr_obj = sf.objects.get(ch_tr_pid)
                if ch_tr_obj:
                    ch_tr_tt = ch_tr_obj.read_typetree()
                    ch_go_pid = ch_tr_tt.get("m_GameObject", {}).get("m_PathID")
                    if ch_go_pid:
                        walk(ch_go_pid, depth + 1)
                        
    walk(root_go[0])

dump_tree(MEG_BUNDLE, "Megatron_Cin_ROTF_lw")
dump_tree(BRAWL_BUNDLE, "brawl_gs_lw")
