# -*- coding: utf-8 -*-
import sys
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

env = UnityPy.load('d:/Agent/tftf/toolchain/unity_build_project/AssetBundles/demolishor_mesh.assetbundle')
for obj in env.objects:
    if obj.type.name == 'Mesh':
        tree = obj.read_typetree()
        if 'demolishor' in tree.get('m_Name', '').lower():
            skin = tree.get('m_Skin', [])
            print(f"Demolishor m_Skin entries: {len(skin)}")
            if skin:
                print("First 3 skin entries:", skin[:3])
            
            bone_hashes = tree.get('m_BoneNameHashes', [])
            print(f"Demolishor m_BoneNameHashes: {len(bone_hashes)}")
            break

env_iron = UnityPy.load('extracted_apk/assets/assetpack/ironhide_cin_rotf_odr/ironhide_cin_rotf.assetbundle')
for obj in env_iron.objects:
    if obj.type.name == 'Mesh':
        tree = obj.read_typetree()
        if tree.get('m_Name') == 'cha_ironhide_cin_rotf_00':
            skin = tree.get('m_Skin', [])
            print(f"\nIronhide m_Skin entries: {len(skin)}")
            bone_hashes = tree.get('m_BoneNameHashes', [])
            print(f"Ironhide m_BoneNameHashes: {len(bone_hashes)}")
            break
