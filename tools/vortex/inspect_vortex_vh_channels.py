import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

env = UnityPy.load('assets_redeco/vortex_gs.assetbundle')
for obj in env.objects:
    if obj.path_id == -2766188856892899435:
        tt = obj.read_typetree()
        vd = tt.get('m_VertexData', {})
        print("Vertex count:", vd.get('m_VertexCount'))
        print("Channels:")
        for ch in vd.get('m_Channels', []):
            print(" ", ch)
