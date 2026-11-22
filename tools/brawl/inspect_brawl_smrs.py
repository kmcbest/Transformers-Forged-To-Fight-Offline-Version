import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

env = UnityPy.load('assets_redeco/brawl_gs.assetbundle')
for obj in env.objects:
    if obj.type.name == 'SkinnedMeshRenderer':
        tt = obj.read_typetree()
        mesh_ptr = tt.get('m_Mesh', {})
        mat_ptrs = tt.get('m_Materials', [])
        print(f"SMR PID {obj.path_id}: Mesh {mesh_ptr.get('m_PathID')}, Mats {[m.get('m_PathID') for m in mat_ptrs]}")
