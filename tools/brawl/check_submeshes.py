import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

BASE_DIR = Path(r"E:\Agent\TFTF-blender")
MESH_BUNDLE = BASE_DIR / r"toolchain\unity_build_project\AssetBundles\brawl_mesh.assetbundle"
DONOR_BUNDLE = BASE_DIR / r"extracted_apk\assets\assetpack\megatron_cin_rotf_odr\megatron_cin_rotf.assetbundle"

env_m = UnityPy.load(str(MESH_BUNDLE))
for o in env_m.objects:
    if o.type.name == "Mesh":
        tt = o.read_typetree()
        print(f"Brawl Mesh '{tt['m_Name']}' submeshes: {len(tt.get('m_SubMeshes', []))}")

env_d = UnityPy.load(str(DONOR_BUNDLE))
for o in env_d.objects:
    if o.type.name == "Mesh":
        tt = o.read_typetree()
        print(f"Donor Mesh '{tt['m_Name']}' submeshes: {len(tt.get('m_SubMeshes', []))}")
