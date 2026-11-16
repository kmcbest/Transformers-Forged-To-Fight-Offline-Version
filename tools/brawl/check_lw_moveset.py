import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy, json

BRAWL_BUNDLE = Path(r"E:\Agent\TFTF-blender\assets_redeco\brawl_gs.assetbundle")
env = UnityPy.load(str(BRAWL_BUNDLE))
sf = list(env.assets)[0]

cobj = sf.objects.get(7896672020251203967)
ctt = cobj.read_typetree()
print("Moves on brawl_gs_lw MoveSet (PID=7896672020251203967):")
for m in ctt.get("_moves", []):
    print(f"  state='{m.get('_animStateName')}', name='{m.get('_name')}', asset={m.get('_asset')}")
