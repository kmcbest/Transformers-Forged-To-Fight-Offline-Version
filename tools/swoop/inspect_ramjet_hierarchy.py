import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\ramjet_gs_deluxe2008_odr\ramjet_gs_deluxe2008.assetbundle")
env = UnityPy.load(str(bundle_path))

for obj in env.objects:
    if obj.type.name == "GameObject":
        data = obj.read()
        name = getattr(data, "m_Name", getattr(data, "name", ""))
        if "ramjet" in name.lower() and not "lw" in name.lower():
            print(f"Root: {name}")
            # print children
            for tr_ptr in data.m_Transform.read().m_Children:
                child_tr = tr_ptr.read()
                child_go = child_tr.m_GameObject.read()
                print(f"  Child: {child_go.m_Name}")
                for sub_ptr in child_tr.m_Children:
                    sub_tr = sub_ptr.read()
                    sub_go = sub_tr.m_GameObject.read()
                    print(f"    Sub: {sub_go.m_Name}")
