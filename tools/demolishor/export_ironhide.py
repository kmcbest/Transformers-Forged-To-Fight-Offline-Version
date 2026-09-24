# -*- coding: utf-8 -*-
import sys
from pathlib import Path
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

bundle_path = "extracted_apk/assets/assetpack/ironhide_cin_rotf_odr/ironhide_cin_rotf.assetbundle"
env = UnityPy.load(bundle_path)

out_dir = Path("tools/demolishor/ironhide_extracted")
out_dir.mkdir(parents=True, exist_ok=True)

for obj in env.objects:
    if obj.type.name == "Mesh":
        mesh = obj.read()
        if mesh.m_Name == "cha_ironhide_cin_rotf_00":
            print(f"Exporting {mesh.m_Name}...")
            # mesh.export() returns a string/bytes representation or exports to file
            try:
                res = mesh.export()
                if isinstance(res, str):
                    (out_dir / f"{mesh.m_Name}.obj").write_text(res, encoding='utf-8')
                    print(f"[✓] Saved {mesh.m_Name}.obj (text, len {len(res)})")
                elif isinstance(res, bytes):
                    (out_dir / f"{mesh.m_Name}.obj").write_bytes(res)
                    print(f"[✓] Saved {mesh.m_Name}.obj (bytes, len {len(res)})")
            except Exception as e:
                print(f"[!] Error exporting mesh: {e}")
            break
