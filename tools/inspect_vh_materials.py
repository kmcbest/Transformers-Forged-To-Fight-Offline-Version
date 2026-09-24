# -*- coding: utf-8 -*-
import sys
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

env = UnityPy.load('extracted_apk/assets/assetpack/ironhide_cin_rotf_odr/ironhide_cin_rotf.assetbundle')

# Map PathID to names
names = {}
for o in env.objects:
    if o.type.name in ('GameObject', 'Material', 'Texture2D', 'Mesh'):
        names[o.path_id] = o.read_typetree().get('m_Name')

for o in env.objects:
    if o.type.name == 'SkinnedMeshRenderer':
        tree = o.read_typetree()
        mesh_pid = tree.get('m_Mesh', {}).get('m_PathID')
        mesh_name = names.get(mesh_pid)
        if mesh_name == 'cha_ironhide_cin_rotf_01':
            print("Found SMR for cha_ironhide_cin_rotf_01:")
            mats = tree.get('m_Materials', [])
            for m_ptr in mats:
                mat_pid = m_ptr.get('m_PathID')
                mat_name = names.get(mat_pid, f"Unknown_{mat_pid}")
                print(f"  Material: '{mat_name}' (PID: {mat_pid})")
                for m_obj in env.objects:
                    if m_obj.path_id == mat_pid and m_obj.type.name == 'Material':
                        m_tree = m_obj.read_typetree()
                        tex_envs = m_tree.get('m_SavedProperties', {}).get('m_TexEnvs', [])
                        for te in tex_envs:
                            if isinstance(te, (tuple, list)):
                                prop_name = te[0]
                                tex_ptr = te[1].get('m_Texture', {}).get('m_PathID') if isinstance(te[1], dict) else getattr(te[1], 'm_Texture', {}).get('m_PathID')
                            elif isinstance(te, dict):
                                prop_name = te.get('first', {}).get('name') if isinstance(te.get('first'), dict) else te.get('first')
                                tex_ptr = te.get('second', {}).get('m_Texture', {}).get('m_PathID')
                            else:
                                continue
                            tex_name = names.get(tex_ptr, f"None_{tex_ptr}")
                            print(f"    Texture slot: '{prop_name}' -> '{tex_name}'")
