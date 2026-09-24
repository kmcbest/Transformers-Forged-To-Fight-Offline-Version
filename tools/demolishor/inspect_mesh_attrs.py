# -*- coding: utf-8 -*-
import sys
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

env = UnityPy.load('extracted_apk/assets/assetpack/ironhide_cin_rotf_odr/ironhide_cin_rotf.assetbundle')
for obj in env.objects:
    if obj.type.name == 'Mesh':
        data = obj.read()
        if data.m_Name == 'cha_ironhide_cin_rotf_00':
            print("Attributes of Mesh object:")
            for attr in dir(data):
                if not attr.startswith('_'):
                    print(" ", attr)
            break
