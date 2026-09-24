# -*- coding: utf-8 -*-
import sys
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

env = UnityPy.load('extracted_apk/assets/assetpack/ironhide_cin_rotf_odr/ironhide_cin_rotf.assetbundle')
for obj in env.objects:
    if obj.type.name == 'Texture2D':
        tree = obj.read_typetree()
        print(f"Texture2D: '{tree.get('m_Name')}', size=({tree.get('m_Width')}x{tree.get('m_Height')}), format={tree.get('m_TextureFormat')}")
