# -*- coding: utf-8 -*-
import sys
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

env = UnityPy.load('extracted_apk/assets/assetpack/ironhide_cin_rotf_odr/ironhide_cin_rotf.assetbundle')
for obj in env.objects:
    if obj.type.name == 'Mesh':
        m = obj.read()
        if m.m_Name == 'cha_ironhide_cin_rotf_00':
            res = m.export()
            print("Export result type:", type(res))
            if isinstance(res, str):
                print("First 200 chars of export:")
                print(res[:200])
            break
