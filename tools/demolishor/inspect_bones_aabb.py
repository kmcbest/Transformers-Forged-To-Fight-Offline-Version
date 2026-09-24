# -*- coding: utf-8 -*-
import sys
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

env_iron = UnityPy.load('extracted_apk/assets/assetpack/ironhide_cin_rotf_odr/ironhide_cin_rotf.assetbundle')
for obj in env_iron.objects:
    if obj.type.name == 'Mesh':
        tree = obj.read_typetree()
        if tree.get('m_Name') == 'cha_ironhide_cin_rotf_00':
            print("Ironhide m_LocalAABB:", tree.get('m_LocalAABB'))
            aabb_list = tree.get('m_BonesAABB', [])
            print(f"Ironhide m_BonesAABB count: {len(aabb_list)}")
            if aabb_list:
                print("First 3 bones AABB:", aabb_list[:3])
            break

env_demo = UnityPy.load('d:/Agent/tftf/toolchain/unity_build_project/AssetBundles/demolishor_mesh.assetbundle')
for obj in env_demo.objects:
    if obj.type.name == 'Mesh':
        tree = obj.read_typetree()
        if 'demolishor' in tree.get('m_Name', '').lower():
            print("\nDemolishor m_LocalAABB:", tree.get('m_LocalAABB'))
            aabb_list = tree.get('m_BonesAABB', [])
            print(f"Demolishor m_BonesAABB count: {len(aabb_list)}")
            if aabb_list:
                print("First 3 bones AABB:", aabb_list[:3])
            break
