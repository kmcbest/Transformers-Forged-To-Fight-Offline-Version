import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

DONOR_BUNDLE = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatronus_gs_kabam_odr\megatronus_gs_kabam.assetbundle")
env = UnityPy.load(str(DONOR_BUNDLE))

for o in env.objects:
    if o.type.name == "Mesh":
        tt = o.read_typetree()
        submeshes = tt.get("m_SubMeshes", [])
        print(f"Donor Mesh '{tt['m_Name']}' submesh count = {len(submeshes)}")
