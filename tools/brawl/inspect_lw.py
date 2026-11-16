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

obj = sf.objects.get(7253228804562187563)
tt = obj.read_typetree()
print("brawl_gs_lw.prefab root:")
for k, v in tt.items():
    if k != "m_Component":
        print(f"  {k}: {v}")
    else:
        print(f"  m_Component count: {len(v)}")
        for item in v:
            cpid = item["component"]["m_PathID"]
            cobj = sf.objects.get(cpid)
            ctype = cobj.type.name if cobj else "MISSING"
            print(f"    PID {cpid}: {ctype}")
