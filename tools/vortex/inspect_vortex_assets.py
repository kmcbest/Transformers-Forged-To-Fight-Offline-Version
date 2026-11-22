import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

env = UnityPy.load('assets_redeco/vortex_gs.assetbundle')
for obj in env.objects:
    if obj.type.name in ('Material', 'Texture2D', 'SkinnedMeshRenderer', 'Mesh'):
        tt = obj.read_typetree()
        name = tt.get('m_Name', '')
        if obj.type.name == 'Material':
            print(f"Material: {name} (PID {obj.path_id})")
            tex_envs = tt.get('m_SavedProperties', {}).get('m_TexEnvs', [])
            for te in tex_envs:
                prop = te[0]
                tex_ptr = te[1].get('m_Texture', {})
                print(f"  Tex: {prop} -> {tex_ptr}")
            cols = tt.get('m_SavedProperties', {}).get('m_Colors', [])
            for c in cols:
                if 'col' in c[0].lower() or 'color' in c[0].lower():
                    print(f"  Col: {c[0]} -> {c[1]}")
            floats = tt.get('m_SavedProperties', {}).get('m_Floats', [])
            for f in floats:
                if 'emissive' in f[0].lower():
                    print(f"  Float: {f[0]} -> {f[1]}")
        elif obj.type.name == 'Texture2D':
            print(f"Texture2D: {name} (PID {obj.path_id}) size={tt.get('m_Width')}x{tt.get('m_Height')}")
        elif obj.type.name == 'SkinnedMeshRenderer':
            print(f"SMR PID {obj.path_id}: mesh={tt.get('m_Mesh')}, mats={tt.get('m_Materials')}")
