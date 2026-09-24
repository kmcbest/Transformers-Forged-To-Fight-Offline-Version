# -*- coding: utf-8 -*-
import sys
from pathlib import Path
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

bundle_path = "extracted_apk/assets/assetpack/ironhide_cin_rotf_odr/ironhide_cin_rotf.assetbundle"
env = UnityPy.load(bundle_path)

for obj in env.objects:
    if obj.type.name == "Mesh":
        mesh = obj.read()
        print(f"Mesh: {mesh.m_Name}, has export: {hasattr(mesh, 'export')}")
        if hasattr(mesh, 'export'):
            print("  export method:", type(mesh.export))
        break

for obj in env.objects:
    if obj.type.name == "GameObject":
        go = obj.read()
        if "ironhide" in go.m_Name.lower():
            print(f"Root GameObject: {go.m_Name}, PathID: {obj.path_id}")
