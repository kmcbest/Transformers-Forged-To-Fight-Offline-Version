import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
env = UnityPy.load(r"e:\Agent\TFTF-blender\assets_redeco\vortex_gs.assetbundle")
for pid in [6239694728433603131, -8672171104083879485, 5741437468734501436]:
    o = [x for x in env.objects if x.path_id == pid][0]
    t = o.read()
    tt = o.read_typetree()
    print(f"Tex {t.m_Name} ({pid}): {t.m_Width}x{t.m_Height}, fmt={t.m_TextureFormat}, mips={tt.get('m_MipCount')}, stream={tt.get('m_StreamData')}, wrap=({tt['m_TextureSettings']['m_WrapU']},{tt['m_TextureSettings']['m_WrapV']})")
