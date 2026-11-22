import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

env = UnityPy.load('assets_redeco/vortex_gs.assetbundle')
for obj in env.objects:
    if obj.type.name == 'Texture2D':
        tt = obj.read_typetree()
        print(f"Texture2D: {tt.get('m_Name')} (PID {obj.path_id})")
