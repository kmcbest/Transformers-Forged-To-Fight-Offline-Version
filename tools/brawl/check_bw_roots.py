import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

BASE_DIR = Path(r"E:\Agent\TFTF-blender")
BW_BUNDLE = BASE_DIR / r"assets_redeco\blitzwing_gs.assetbundle"
env = UnityPy.load(str(BW_BUNDLE))

for o in env.objects:
    if o.type.name == "AssetBundle":
        tt = o.read_typetree()
        for k, v in tt.get("m_Container", []):
            pid = v["asset"]["m_PathID"]
            for o2 in env.objects:
                if o2.path_id == pid:
                    print(f"Container: {k} -> GO Name: {o2.read_typetree().get('m_Name')}")
