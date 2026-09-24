# -*- coding: utf-8 -*-
import sys
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

env = UnityPy.load('extracted_apk/assets/assetpack/ironhide_cin_rotf_odr/ironhide_cin_rotf.assetbundle')
go_map = {}
for o in env.objects:
    if o.type.name == 'GameObject':
        go_map[o.path_id] = o.read_typetree().get('m_Name')

for o in env.objects:
    if o.type.name == 'SkinnedMeshRenderer':
        tree = o.read_typetree()
        go_pid = tree.get('m_GameObject', {}).get('m_PathID')
        mesh_pid = tree.get('m_Mesh', {}).get('m_PathID')
        mesh_name = "Unknown"
        for m in env.objects:
            if m.path_id == mesh_pid:
                mesh_name = m.read_typetree().get('m_Name')
                break
        print(f"SMR on GO: '{go_map.get(go_pid)}' -> uses Mesh: '{mesh_name}'")
