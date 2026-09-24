# -*- coding: utf-8 -*-
import sys
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

env = UnityPy.load('extracted_apk/assets/assetpack/ironhide_cin_rotf_odr/ironhide_cin_rotf.assetbundle')
go_names = {}
tr_to_go = {}
for obj in env.objects:
    if obj.type.name == 'GameObject':
        go_names[obj.path_id] = obj.read_typetree().get('m_Name')
    elif obj.type.name == 'Transform':
        tree = obj.read_typetree()
        tr_to_go[obj.path_id] = tree.get('m_GameObject', {}).get('m_PathID')

iron_bones = []
for obj in env.objects:
    if obj.type.name == 'SkinnedMeshRenderer':
        tree = obj.read_typetree()
        mesh_ptr = tree.get('m_Mesh', {}).get('m_PathID')
        # find cha_ironhide_cin_rotf_00
        for m_obj in env.objects:
            if m_obj.path_id == mesh_ptr and m_obj.read_typetree().get('m_Name') == 'cha_ironhide_cin_rotf_00':
                for b in tree.get('m_Bones', []):
                    iron_bones.append(go_names.get(tr_to_go.get(b.get('m_PathID'))))
                break
        if iron_bones:
            break

print("Ironhide 80 bones with indices:")
for idx, b in enumerate(iron_bones):
    print(f"  {idx:2d}: {b}")
