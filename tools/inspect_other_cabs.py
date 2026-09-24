# -*- coding: utf-8 -*-
import sys
from pathlib import Path
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

for p in Path("assets_redeco").glob("*.assetbundle"):
    if p.stem in ("demolishor_gs", "optimus_sg", "starsaber", "dragstrip_gs", "wildrider_gs", "breakdown_gs"):
        env = UnityPy.load(str(p))
        cabs = []
        for obj in env.objects:
            if hasattr(obj, "assets_file") and getattr(obj.assets_file, "name", "").startswith("CAB-"):
                if obj.assets_file.name not in cabs:
                    cabs.append(obj.assets_file.name)
        print(f"Bundle {p.name}: CABs = {cabs}")
