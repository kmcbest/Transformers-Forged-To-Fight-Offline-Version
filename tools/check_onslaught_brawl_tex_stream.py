import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

for bname in ["onslaught_gs.assetbundle", "brawl_gs.assetbundle"]:
    env = UnityPy.load(rf"e:\Agent\TFTF-blender\assets_redeco\{bname}")
    print(f"=== {bname} Texture2D stream check ===")
    for o in env.objects:
        if o.type.name == "Texture2D":
            t = o.read()
            tt = o.read_typetree()
            sd = tt.get("m_StreamData", {})
            if "RAOE" in t.m_Name or "main" in t.m_Name or "tform" in t.m_Name:
                print(f"  {t.m_Name} ({o.path_id}): {t.m_Width}x{t.m_Height}, fmt={t.m_TextureFormat}, stream_size={sd.get('size', 0)}")
