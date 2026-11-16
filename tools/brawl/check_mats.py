import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

BASE_DIR = Path(r"E:\Agent\TFTF-blender")
DONOR = BASE_DIR / r"extracted_apk\assets\assetpack\megatron_cin_rotf_odr\megatron_cin_rotf.assetbundle"
env = UnityPy.load(str(DONOR))
obj_map = {o.path_id: o for o in env.objects}

for pid in [2758279787216392959, -8143696719442631496, -7777457830161264517, -7854615674899395621]:
    o = obj_map.get(pid)
    if o:
        tt = o.read_typetree()
        shader = tt.get("m_Shader", {})
        print(f"PID={pid} Name='{tt.get('m_Name')}' Shader={shader}")
    else:
        print(f"PID={pid} NOT FOUND!")
