# -*- coding: utf-8 -*-
import sys
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

env = UnityPy.load('extracted_apk/assets/assetpack/ironhide_cin_rotf_odr/ironhide_cin_rotf.assetbundle')
for o in env.objects:
    if o.type.name == 'Mesh':
        tree = o.read_typetree()
        name = tree.get('m_Name')
        if name in ('cha_ironhide_cin_rotf_00', 'cha_ironhide_cin_rotf_01'):
            aabb = tree.get('m_LocalAABB', {})
            print(f"Mesh '{name}':")
            print(f"  Submeshes: {len(tree.get('m_SubMeshes', []))}")
            print(f"  AABB Center: {aabb.get('m_Center')}, Extent: {aabb.get('m_Extent')}")
            print(f"  BindPoses count: {len(tree.get('m_BindPose', []))}")
