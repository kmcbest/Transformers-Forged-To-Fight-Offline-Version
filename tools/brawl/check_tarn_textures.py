import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

BASE_DIR = Path(r"E:\Agent\TFTF-blender")
TARN_BUNDLE = BASE_DIR / r"assets_redeco\tarn_gs.assetbundle"
env = UnityPy.load(str(TARN_BUNDLE))

for o in env.objects:
    if o.type.name == "Texture2D":
        tt = o.read_typetree()
        data = o.read()
        img_len = len(data.image_data) if hasattr(data, 'image_data') else 'N/A'
        sd = tt.get("m_StreamData")
        print(f"Tarn Tex PID={o.path_id} Name='{tt.get('m_Name')}' Format={tt.get('m_TextureFormat')} ImageDataLen={img_len} StreamData={sd} MipCount={tt.get('m_MipCount')}")
