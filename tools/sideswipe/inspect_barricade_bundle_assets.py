import os
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import UnityPy

BUNDLE_PATH = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\barricade_cin_dotm_odr\barricade_cin_dotm.assetbundle"
env = UnityPy.load(BUNDLE_PATH)

print("GameObjects in Barricade bundle:")
for o in env.objects:
    if o.type.name == "GameObject":
        tt = o.read_typetree()
        print(f"  GO: {tt.get('m_Name')} (pid={o.path_id})")

print("\nMeshes in Barricade bundle:")
for o in env.objects:
    if o.type.name == "Mesh":
        tt = o.read_typetree()
        print(f"  Mesh: {tt.get('m_Name')} (pid={o.path_id})")

print("\nTextures in Barricade bundle:")
for o in env.objects:
    if o.type.name == "Texture2D":
        tt = o.read_typetree()
        print(f"  Tex: {tt.get('m_Name')} (pid={o.path_id})")

print("\nAssetBundle m_Container:")
for o in env.objects:
    if o.type.name == "AssetBundle":
        tt = o.read_typetree()
        for k, v in tt.get("m_Container", []):
            print(f"  Container: {k} -> {v.get('asset', {}).get('m_PathID')}")
