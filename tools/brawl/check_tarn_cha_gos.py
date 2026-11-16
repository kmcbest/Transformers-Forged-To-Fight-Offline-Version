import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

BASE_DIR = Path(r"E:\Agent\TFTF-blender")
TARN_BUNDLE = BASE_DIR / r"assets_redeco\tarn_gs.assetbundle"
env_t = UnityPy.load(str(TARN_BUNDLE))

for o in env_t.objects:
    if o.type.name == "GameObject":
        name = o.read_typetree().get("m_Name", "")
        if "cha_" in name:
            print(f"Tarn GO PID={o.path_id} Name={name}")
