# -*- coding: utf-8 -*-
import sys
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

print("--- Inspecting ironhide_cin_rotf.assetbundle ---")
i_env = UnityPy.load("extracted_apk/assets/assetpack/ironhide_cin_rotf_odr/ironhide_cin_rotf.assetbundle")
for obj in i_env.objects:
    if hasattr(obj, "assets_file") and getattr(obj.assets_file, "name", "").startswith("CAB-"):
        print(f"Ironhide CAB: {obj.assets_file.name}")
        break

print("\n--- Inspecting demolishor_gs.assetbundle ---")
d_env = UnityPy.load("assets_redeco/demolishor_gs.assetbundle")
for obj in d_env.objects:
    if hasattr(obj, "assets_file") and getattr(obj.assets_file, "name", "").startswith("CAB-"):
        print(f"Demolishor CAB: {obj.assets_file.name}")
        break

print("\n--- Inspecting Demolishor AssetBundle container table ---")
for obj in d_env.objects:
    if obj.type.name == "AssetBundle":
        ab = obj.read_typetree()
        for item in ab.get("m_Container", []):
            print(f"  Container entry: {item[0]} -> PathID {item[1].get('asset', {}).get('m_PathID')}")

print("\n--- Inspecting Ironhide AssetBundle container table ---")
for obj in i_env.objects:
    if obj.type.name == "AssetBundle":
        ab = obj.read_typetree()
        for item in ab.get("m_Container", []):
            print(f"  Container entry: {item[0]} -> PathID {item[1].get('asset', {}).get('m_PathID')}")
