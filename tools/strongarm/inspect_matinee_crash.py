import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

p_orig = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\prowl_gs_deluxe2016_odr\prowl_gs_deluxe2016.assetbundle")
p_reg = Path(r"E:\Agent\TFTF-blender\toolchain\prowl_anims_registered.assetbundle")
p_sa = Path(r"E:\Agent\TFTF-blender\assets_redeco\strongarm_gs.assetbundle")

def check_bundle(p, label):
    print(f"\n=== {label}: {p.name} ===")
    env = UnityPy.load(str(p))
    ab = next(o.read_typetree() for o in env.objects if o.type.name == "AssetBundle")
    print(f"m_Container count: {len(ab.get('m_Container', []))}")
    print(f"m_PreloadTable count: {len(ab.get('m_PreloadTable', []))}")
    
    # Inspect MonoBehaviours mentioning clip or animator or Matinee
    scripts = {}
    gos = {}
    for o in env.objects:
        if o.type.name == "MonoScript":
            t = o.read_typetree()
            scripts[o.path_id] = t.get("m_ClassName", "")
        elif o.type.name == "GameObject":
            t = o.read_typetree()
            gos[o.path_id] = t.get("m_Name", "")

    for o in env.objects:
        if o.type.name == "MonoBehaviour":
            t = o.read_typetree()
            sc_pid = t.get("m_Script", {}).get("m_PathID", 0)
            sc_name = scripts.get(sc_pid, f"Ext_{t.get('m_Script', {}).get('m_FileID')}_{sc_pid}")
            go_pid = t.get("m_GameObject", {}).get("m_PathID", 0)
            go_name = gos.get(go_pid, "?")
            if "matinee" in go_name.lower() or "special" in go_name.lower() or "prowl" in go_name.lower() or "strongarm" in go_name.lower() or "Animation" in str(t) or "Clip" in str(t):
                # summarize keys & values
                interesting = {k: v for k, v in t.items() if k not in ("m_GameObject", "m_Enabled", "m_Script", "m_Name")}
                print(f"  MB PID={o.path_id} GO='{go_name}' script='{sc_name}' -> keys={list(interesting.keys())}")
                for k, v in interesting.items():
                    if isinstance(v, (str, int, float, bool)) or (isinstance(v, dict) and "m_PathID" in v):
                        print(f"     {k}: {v}")

check_bundle(p_orig, "PROWL OFFICIAL")
check_bundle(p_reg, "PROWL REGISTERED")
check_bundle(p_sa, "STRONGARM CURRENT")
