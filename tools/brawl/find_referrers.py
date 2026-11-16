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

target_pids = {2367818045411061912, -7777457830161264517, -7854615674899395621, -62711741483785396}

def iter_pptrs(node):
    if isinstance(node, dict):
        if "m_PathID" in node:
            yield node["m_PathID"]
        else:
            for v in node.values():
                yield from iter_pptrs(v)
    elif isinstance(node, (list, tuple)):
        for x in node:
            yield from iter_pptrs(x)

for o in env.objects:
    try:
        tt = o.read_typetree()
        for ref in iter_pptrs(tt):
            if ref in target_pids:
                print(f"Object PID={o.path_id} Type={o.type.name} Name='{tt.get('m_Name')}' references {ref}")
    except:
        pass
