import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
TARN_BUNDLE = ROOT / "assets_redeco" / "tarn_gs.assetbundle"

env = UnityPy.load(str(TARN_BUNDLE))
sf = list(env.assets)[0]

for pid, obj in sf.objects.items():
    if obj.type.name == "GameObject":
        tt = obj.read_typetree()
        name = tt.get("m_Name", "")
        if "tarn" in name.lower() or "ultra" in name.lower():
            print(f"GO PID={pid}: name='{name}'")
