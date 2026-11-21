import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF")
for p in (ROOT / "extracted_apk" / "assets" / "assetpack").rglob("*.assetbundle"):
    try:
        env = UnityPy.load(str(p))
        cabs = [k for k in env.file.files.keys() if "48a8" in k.lower()]
        if cabs:
            print(f"Found CAB in: {p.name} -> {cabs}")
            for o in env.objects:
                if o.path_id in (-9189341399945500108, 6713440653250120606, 2036210894060600181, 2583143826113944820):
                    print(f"  {o.path_id}: {o.type.name} {o.read_typetree().get('m_Name')}")
            break
    except Exception:
        pass
