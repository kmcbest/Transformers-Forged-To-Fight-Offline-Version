# -*- coding: utf-8 -*-
import sys
from pathlib import Path
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

bundle_path = "extracted_apk/assets/assetpack/ironhide_cin_rotf_odr/ironhide_cin_rotf.assetbundle"
env = UnityPy.load(bundle_path)

for obj in env.objects:
    if obj.type.name == "Mesh":
        tree = obj.read_typetree()
        if tree.get("m_Name") == "cha_ironhide_cin_rotf_00":
            skin = tree.get("m_Skin", [])
            bindpose = tree.get("m_BindPose", [])
            print(f"Mesh {tree.get('m_Name')}:")
            print(f"  Skin entries count: {len(skin)}")
            print(f"  BindPoses count: {len(bindpose)}")
            if skin:
                print("  Skin sample 0:", skin[0])
            if bindpose:
                print("  BindPose sample 0:", bindpose[0])
            break
