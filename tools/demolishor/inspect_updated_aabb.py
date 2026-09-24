# -*- coding: utf-8 -*-
import sys
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

env = UnityPy.load('assets_redeco/demolishor_gs.assetbundle')
for obj in env.objects:
    if obj.type.name == 'Mesh':
        tree = obj.read_typetree()
        if tree.get('m_Name') == 'cha_ironhide_cin_rotf_00':
            print("Local AABB Center:", tree.get('m_LocalAABB', {}).get('m_Center'))
            print("Local AABB Extent:", tree.get('m_LocalAABB', {}).get('m_Extent'))
            break
