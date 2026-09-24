# -*- coding: utf-8 -*-
import sys
from pathlib import Path
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

env = UnityPy.load('extracted_apk/assets/assetpack/ironhide_cin_rotf_odr/ironhide_cin_rotf.assetbundle')
for obj in env.objects:
    if obj.type.name == 'Mesh':
        m = obj.read()
        if m.m_Name == 'cha_ironhide_cin_rotf_00':
            out_obj = Path("tools/demolishor/ironhide_extracted/ironhide.obj")
            out_obj.parent.mkdir(parents=True, exist_ok=True)
            with open(out_obj, "w", encoding="utf-8") as f:
                f.write(m.export())
            print(f"[✓] Exported Ironhide OBJ to {out_obj} ({out_obj.stat().st_size} bytes)")
            break
