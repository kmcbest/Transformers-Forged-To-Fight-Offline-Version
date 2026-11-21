import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

ROOT = Path(r"E:\Agent\TFTF-blender")
env_ss = UnityPy.load(str(ROOT / "assets_redeco" / "sideswipe_cin_rotf.assetbundle"))
sf_ss = list(env_ss.assets)[0]

moveset_obj = sf_ss.objects[-5126079019749064592]
tt = moveset_obj.read_typetree()
for idx, m in enumerate(tt.get("_moves", [])):
    print(f"[{idx:02d}] {m.get('_name')}: {m.get('_asset')}")
