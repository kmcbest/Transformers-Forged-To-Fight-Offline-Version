# -*- coding: utf-8 -*-
import sys
import json
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

env = UnityPy.load('extracted_apk/assets/assetpack/ironhide_cin_rotf_odr/ironhide_cin_rotf.assetbundle')

go_names = {}
for o in env.objects:
    if o.type.name == 'GameObject':
        go_names[o.path_id] = o.read_typetree().get('m_Name')

path_to_name = {}
for o in env.objects:
    if o.type.name == 'Transform':
        t = o.read_typetree()
        go_pid = t.get('m_GameObject', {}).get('m_PathID')
        path_to_name[o.path_id] = go_names.get(go_pid, f"Unknown_{go_pid}")

for o in env.objects:
    if o.type.name == 'SkinnedMeshRenderer':
        tree = o.read_typetree()
        mesh_pid = tree.get('m_Mesh', {}).get('m_PathID')
        for m in env.objects:
            if m.path_id == mesh_pid and m.read_typetree().get('m_Name') == 'cha_ironhide_cin_rotf_01':
                bones = [path_to_name.get(b.get('m_PathID')) for b in tree.get('m_Bones', [])]
                print(f"Vehicle SMR bones ({len(bones)}):")
                for i, b in enumerate(bones):
                    print(f"  [{i:02d}] {b}")
                break
