import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
BRAWL_BUNDLE = ROOT / "assets_redeco" / "brawl_gs.assetbundle"
MEG_BUNDLE = ROOT / "extracted_apk" / "assets" / "assetpack" / "megatron_cin_rotf_odr" / "megatron_cin_rotf.assetbundle"
TARN_BUNDLE = ROOT / "assets_redeco" / "tarn_gs.assetbundle"

def inspect_lw(bundle_path, label):
    print(f"\n=================== {label}: {bundle_path.name} ===================")
    env = UnityPy.load(str(bundle_path))
    sf = list(env.assets)[0]
    
    # Find AssetBundle object
    ab = next(o for o in sf.objects.values() if o.type.name == "AssetBundle").read_typetree()
    print("Container entries:")
    for k, v in ab["m_Container"]:
        print(f"  {k} -> asset PathID={v['asset']['m_PathID']}, preloadIndex={v['preloadIndex']}, preloadSize={v['preloadSize']}")
    
    # Find _lw GameObject
    lw_go = None
    for pid, o in sf.objects.items():
        if o.type.name == "GameObject":
            tt = o.read_typetree()
            if tt["m_Name"].endswith("_lw"):
                lw_go = (pid, tt)
                break
    
    if not lw_go:
        print("NO _lw GameObject found!")
        return

    pid, go_tt = lw_go
    print(f"\n_lw GameObject: '{go_tt['m_Name']}' (PID={pid})")
    print(f"Components on {go_tt['m_Name']}:")
    for comp in go_tt.get("m_Component", []):
        c_pid = comp["component"]["m_PathID"]
        c_obj = sf.objects.get(c_pid)
        c_type = c_obj.type.name if c_obj else "UNKNOWN"
        print(f"  Component PID={c_pid}: type={c_type}")
        if c_type == "Animator":
            att = c_obj.read_typetree()
            print(f"    Avatar: {att.get('m_Avatar')}")
            print(f"    Controller: {att.get('m_Controller')}")
        elif c_type == "MonoBehaviour":
            mtt = c_obj.read_typetree()
            m_script = mtt.get("m_Script", {})
            print(f"    MonoScript: FileID={m_script.get('m_FileID')}, PathID={m_script.get('m_PathID')}")
            # print first few keys
            print(f"    Keys: {list(mtt.keys())[:8]}")

inspect_lw(BRAWL_BUNDLE, "BRAWL")
inspect_lw(MEG_BUNDLE, "MEGATRON (DONOR)")
inspect_lw(TARN_BUNDLE, "TARN (WORKING)")
