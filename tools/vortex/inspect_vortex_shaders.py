import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

env = UnityPy.load('assets_redeco/vortex_gs.assetbundle')
for obj in env.objects:
    if obj.type.name == 'Material':
        tt = obj.read_typetree()
        name = tt.get('m_Name')
        shader = tt.get('m_Shader')
        print(f"Material: {name} (PID {obj.path_id}) -> Shader: {shader}")
