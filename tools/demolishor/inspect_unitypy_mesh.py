# -*- coding: utf-8 -*-
import sys
import inspect
from pathlib import Path
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

bundle_path = "extracted_apk/assets/assetpack/ironhide_cin_rotf_odr/ironhide_cin_rotf.assetbundle"
env = UnityPy.load(bundle_path)

for obj in env.objects:
    if obj.type.name == "Mesh":
        mesh = obj.read()
        if mesh.m_Name == "cha_ironhide_cin_rotf_00":
            print("Mesh attributes and methods:")
            for a in dir(mesh):
                if not a.startswith("__"):
                    val = getattr(mesh, a)
                    if callable(val):
                        print(f"  method: {a}() -> {inspect.signature(val)}")
                    else:
                        print(f"  field: {a} = {type(val)}")
            break
