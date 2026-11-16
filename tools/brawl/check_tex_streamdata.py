import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

BASE_DIR = Path(r"E:\Agent\TFTF-blender")
BRAWL_BUNDLE = BASE_DIR / r"assets_redeco\brawl_gs.assetbundle"
env = UnityPy.load(str(BRAWL_BUNDLE))
obj_map = {o.path_id: o for o in env.objects}

tex_pids = [
    7575930771601290721,
    42717178677652158,
    -8652859075577142890,
    2805008792520890735,
    -3665651547192902677,
    -4057584031439743300,
]

for pid in tex_pids:
    o = obj_map[pid]
    tt = o.read_typetree()
    data = o.read()
    img_len = len(data.image_data) if hasattr(data, 'image_data') else 'N/A'
    sd = tt.get("m_StreamData")
    print(f"Tex PID={pid} Name='{tt.get('m_Name')}' Format={tt.get('m_TextureFormat')} ImageDataLen={img_len} StreamData={sd}")
