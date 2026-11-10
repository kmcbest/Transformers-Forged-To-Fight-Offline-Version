import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

def dump_matinee(p, label):
    print(f"\n================ {label} ================")
    env = UnityPy.load(str(p))
    gos = {o.path_id: o.read_typetree().get("m_Name", "") for o in env.objects if o.type.name == "GameObject"}
    scripts = {o.path_id: o.read_typetree().get("m_ClassName", "") for o in env.objects if o.type.name == "MonoScript"}
    for o in env.objects:
        if o.type.name == "MonoBehaviour":
            t = o.read_typetree()
            go_name = gos.get(t.get("m_GameObject", {}).get("m_PathID"), "?")
            sc_name = scripts.get(t.get("m_Script", {}).get("m_PathID"), f"PID_{t.get('m_Script', {}).get('m_PathID')}")
            if any(k in sc_name.lower() or k in go_name.lower() for k in ("matinee", "playerref", "animator")):
                print(f"MB PID={o.path_id} GO='{go_name}' script='{sc_name}'")
                for k, v in t.items():
                    if k not in ("m_GameObject", "m_Enabled", "m_Script", "m_Name"):
                        s = str(v)
                        print(f"  {k}: {s[:400]}" + ("..." if len(s) > 400 else ""))
                        if "PlayMecanim" in s or "eid" in s:
                            import json
                            try:
                                if isinstance(v, str) and v.startswith("{"):
                                    d = json.loads(v)
                                    for tk, tv in d.items():
                                        if "track" in tk and not "econtainer" in tk:
                                            print(f"     [track] {tk}: {tv}")
                                        elif "econtainer" in tk and "PlayMecanim" in str(tv):
                                            print(f"     [mecanim] {tk}: {tv}")
                            except Exception:
                                pass

dump_matinee(Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\prowl_gs_deluxe2016_odr\prowl_gs_deluxe2016.assetbundle"), "PROWL OFFICIAL")
dump_matinee(Path(r"E:\Agent\TFTF-blender\assets_redeco\strongarm_gs.assetbundle"), "STRONGARM CURRENT")
dump_matinee(Path(r"E:\Agent\TFTF-blender\assets_redeco\vortex_gs.assetbundle"), "VORTEX WORKING")
