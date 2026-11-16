import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

BRAWL_BUNDLE = Path(r"E:\Agent\TFTF-blender\assets_redeco\brawl_gs.assetbundle")
env = UnityPy.load(str(BRAWL_BUNDLE))
sf = list(env.assets)[0]

obj = sf.objects.get(324365576946399764)
tt = obj.read_typetree()
for item in tt.get("m_Component", []):
    cpid = item["component"]["m_PathID"]
    cobj = sf.objects.get(cpid)
    ctype = cobj.type.name if cobj else "MISSING"
    cname = ""
    if ctype == "MonoBehaviour":
        ctt = cobj.read_typetree()
        cname = ctt.get("m_Name", "")
        # also get script name if possible
        ms = ctt.get("m_Script", {})
        sf_idx = ms.get("m_FileID", 0)
        cname += f" (Script: FileID={sf_idx}, PathID={ms.get('m_PathID')})"
    print(f"  PID {cpid}: {ctype} {cname}")
