# -*- coding: utf-8 -*-
import sys
import numpy as np
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

# Load the compiled Demolishor mesh from Unity
env_demo = UnityPy.load('d:/Agent/tftf/toolchain/unity_build_project/AssetBundles/demolishor_mesh.assetbundle')
for obj in env_demo.objects:
    if obj.type.name == 'Mesh':
        tree = obj.read_typetree()
        if 'demolishor' in tree.get('m_Name', '').lower():
            vdata = tree.get('m_VertexData', {})
            print(f"Demolishor mesh: {tree.get('m_Name')}")
            print(f"Vertex count: {vdata.get('m_VertexCount')}")
            
            # Print bounding box
            aabb = tree.get('m_LocalAABB', {})
            print(f"Local AABB Center: {aabb.get('m_Center')}")
            print(f"Local AABB Extent: {aabb.get('m_Extent')}")
            break

# Also check Ironhide's bounding box
env_iron = UnityPy.load('extracted_apk/assets/assetpack/ironhide_cin_rotf_odr/ironhide_cin_rotf.assetbundle')
for obj in env_iron.objects:
    if obj.type.name == 'Mesh':
        tree = obj.read_typetree()
        if tree.get('m_Name') == 'cha_ironhide_cin_rotf_00':
            aabb = tree.get('m_LocalAABB', {})
            print(f"\nIronhide mesh: {tree.get('m_Name')}")
            print(f"Local AABB Center: {aabb.get('m_Center')}")
            print(f"Local AABB Extent: {aabb.get('m_Extent')}")
            break
