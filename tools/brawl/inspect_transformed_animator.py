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

anim_obj = obj_map[6009558426966370246]
print("Animator 6009558426966370246:")
print(anim_obj.read_typetree())
