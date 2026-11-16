import sys
from pathlib import Path
import UnityPy

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

env = UnityPy.load("assets_redeco/tarn_gs.assetbundle")
for o in env.objects:
    if o.type.name == "Texture2D":
        t = o.read()
        sd = getattr(t, "m_StreamData", None)
        sd_info = f"offset={sd.offset}, size={sd.size}, path='{sd.path}'" if sd else "None"
        raw_len = len(getattr(t, "image_data", b""))
        print(f"Tarn Tex PID={o.path_id}: name='{t.m_Name}', size=({t.m_Width}x{t.m_Height}), format={t.m_TextureFormat}, m_MipCount={t.m_MipCount}, raw_len={raw_len}, StreamData=({sd_info})")
