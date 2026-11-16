import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
MEG_BUNDLE = ROOT / "extracted_apk" / "assets" / "assetpack" / "megatron_cin_rotf_odr" / "megatron_cin_rotf.assetbundle"

env = UnityPy.load(str(MEG_BUNDLE))
sf = list(env.assets)[0]

def iter_pptrs_in_tree(node):
    if isinstance(node, dict):
        if "m_FileID" in node and "m_PathID" in node:
            yield node
        else:
            for v in node.values():
                yield from iter_pptrs_in_tree(v)
    elif isinstance(node, (list, tuple)):
        for x in node:
            yield from iter_pptrs_in_tree(x)

print(f"External 4: {sf.externals[3].name}")
for pid, obj in sf.objects.items():
    try:
        tt = obj.read_typetree()
    except:
        continue
    for pptr in iter_pptrs_in_tree(tt):
        if pptr.get("m_FileID") == 4:
            print(f"Obj PID={pid} ({obj.type.name}) references External 4: PathID={pptr.get('m_PathID')}")
